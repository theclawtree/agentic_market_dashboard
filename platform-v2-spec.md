# Platform V2 — Django SaaS Spec

## Overview
Migrate prediction market dashboard from single-user FastAPI/Jinja2 to a multi-user Django SaaS with Stripe billing, deployed on AWS via Terraform.

## Stack
- **Backend:** Django 5.x + Django REST Framework
- **Database:** PostgreSQL 16 (local dev → RDS in prod)
- **Auth:** Django built-in (email/password, session-based)
- **Payments:** Stripe Checkout + Webhooks ($3.99/mo beta tier)
- **Frontend:** Django templates (port existing Jinja2 → Django template syntax)
- **Data pipeline:** Existing ingest/analysis code, adapted to write to S3 (prod) or local (dev)
- **Deployment:** Docker → AWS ECS Fargate via Terraform
- **IaC:** Terraform (AWS provider)

## Project Structure
```
platform-v2/
├── manage.py
├── Dockerfile
├── docker-compose.yml          # Local dev (Django + Postgres + pipeline worker)
├── requirements.txt
├── config/                     # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py             # Shared settings
│   │   ├── dev.py              # Local dev
│   │   └── prod.py             # AWS production
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/               # User registration, login, profile
│   │   ├── models.py           # Custom User model (email-based login)
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── templates/accounts/
│   ├── billing/                # Stripe subscription management
│   │   ├── models.py           # Subscription, StripeCustomer
│   │   ├── views.py            # Checkout, portal, webhook
│   │   ├── urls.py
│   │   ├── middleware.py       # PaywallMiddleware
│   │   └── webhooks.py
│   └── dashboard/              # Market data views (ported from FastAPI)
│       ├── models.py           # MarketSnapshot, NewsArticle, Opportunity
│       ├── views.py
│       ├── urls.py
│       ├── services.py         # Data loading logic (from parquet/S3/DB)
│       └── templates/dashboard/
├── pipeline/                   # Data ingestion (adapted from existing code)
│   ├── ingest/                 # polymarket.py, kalshi.py (existing)
│   ├── analysis/               # ranking.py, news.py, sentiment.py (existing)
│   ├── management/
│   │   └── commands/
│   │       └── run_pipeline.py # Django management command
│   └── tasks.py                # Pipeline runner
├── templates/                  # Shared base templates
│   ├── base.html
│   ├── landing.html            # Public landing/pricing page
│   └── components/
├── static/
│   ├── css/
│   └── js/
└── terraform/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── modules/
    │   ├── vpc/
    │   ├── ecs/
    │   ├── rds/
    │   ├── alb/
    │   ├── s3/
    │   └── secrets/
    └── environments/
        ├── dev.tfvars
        └── prod.tfvars
```

## Data Models

### accounts.User (AbstractUser)
- email (unique, used for login)
- first_name, last_name
- date_joined
- is_active

### billing.Subscription
- user (FK → User)
- stripe_customer_id
- stripe_subscription_id
- status (active | canceled | past_due | trialing)
- current_period_start
- current_period_end
- created_at

### dashboard.MarketSnapshot
- platform (polymarket | kalshi)
- market_id (external ID)
- question / title
- yes_price, no_price, spread
- volume_24h, liquidity, open_interest
- opportunity_score
- snapshot_time (timestamp)
- Index on (platform, snapshot_time)

### dashboard.NewsArticle
- headline, source, url
- market_question (text)
- sentiment (bullish | bearish | neutral)
- sentiment_score (float)
- relevance (float)
- published_at
- fetched_at

## Auth Flow
1. User signs up (email + password) → Django creates User
2. Redirect to Stripe Checkout ($3.99/mo)
3. Stripe webhook creates Subscription record
4. PaywallMiddleware checks: user logged in + active subscription
5. No subscription → redirect to pricing/checkout page

## Stripe Integration
- **Checkout:** `stripe.checkout.Session.create()` with price ID
- **Webhooks:**
  - `checkout.session.completed` → create Subscription
  - `customer.subscription.updated` → update status
  - `customer.subscription.deleted` → mark canceled
  - `invoice.payment_failed` → mark past_due
- **Customer Portal:** link for users to manage billing
- **Keys:** `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_ID` in env vars

## Paywall Middleware
```python
class PaywallMiddleware:
    EXEMPT_PATHS = ['/', '/accounts/', '/billing/webhook/', '/admin/', '/static/']

    def process_request(self, request):
        if any(request.path.startswith(p) for p in self.EXEMPT_PATHS):
            return None
        if not request.user.is_authenticated:
            return redirect('/accounts/login/')
        if not request.user.has_active_subscription:
            return redirect('/billing/subscribe/')
        return None
```

## Pipeline Adaptation
- Existing ingest/analysis code stays mostly unchanged
- Data writes to PostgreSQL (MarketSnapshot, NewsArticle) instead of parquet
- `python manage.py run_pipeline` replaces `python main.py`
- In prod: ECS scheduled task or separate worker container
- Keep parquet as optional backup (S3)

## AWS Architecture (Terraform)
```
Internet → ALB (HTTPS/443) → ECS Fargate (Django via gunicorn)
                                    ↓
                              RDS PostgreSQL
                                    ↓
                              S3 (static files + data backups)

Secrets Manager → API keys, Stripe keys, DB credentials
CloudWatch → Logs + basic alarms
ECR → Docker image registry
```

### Terraform Resources
- **VPC:** 2 AZs, public subnets only (no NAT gateway — beta cost savings)
- **ECS:** Fargate service, task definition, auto-scaling (min 1, max 3)
- **RDS:** db.t3.micro PostgreSQL, private subnet, 20GB
- **ALB:** Application Load Balancer, HTTP→HTTPS redirect, health checks
- **ACM:** SSL cert (when domain ready)
- **S3:** Static files bucket + data bucket
- **ECR:** Container registry
- **Secrets Manager:** All sensitive config
- **CloudWatch:** Log groups, basic CPU/memory alarms
- **Security Groups:** ALB→ECS (8000), ECS→RDS (5432), ALB←Internet (443)

### Estimated AWS Cost
- ECS Fargate (0.25 vCPU, 0.5GB): ~$10/mo
- RDS db.t3.micro: ~$15/mo
- ALB: ~$16/mo + traffic
- S3 + ECR: ~$1/mo
- **Total: ~$20-45/mo** (public subnets, no NAT gateway for beta)

## Build Order
1. **Phase 1 — Django scaffold + accounts + dashboard port** (get it running locally)
2. **Phase 2 — Stripe billing + paywall middleware**
3. **Phase 3 — Pipeline adaptation** (write to DB instead of parquet)
4. **Phase 4 — Docker + docker-compose** (local prod-like setup)
5. **Phase 5 — Terraform + AWS deployment**

## Dev Setup
```bash
# Prerequisites: Python 3.12+, PostgreSQL, Stripe CLI (for webhook testing)
cd platform-v2
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
createdb predmarket
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Environment Variables
```
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=...
DATABASE_URL=postgres://user:pass@localhost:5432/predmarket
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
NEWS_API_KEY=...
LLM_API_KEY=...
AWS_STORAGE_BUCKET_NAME=...
```
