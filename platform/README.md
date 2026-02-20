# Prediction Market Trading Platform

Local-first data platform for informed prediction market trading. Designed to scale to AWS.

## Architecture

```
platform/
├── config.yaml              # All configurable parameters
├── ingest/
│   ├── polymarket.py        # Polymarket data collector
│   ├── kalshi.py            # Kalshi data collector
│   └── runner.py            # Scheduled ingestion orchestrator
├── storage/
│   ├── writer.py            # Parquet writer (date/time partitioned)
│   ├── reader.py            # Parquet reader + query helpers
│   └── cleanup.py           # Auto-delete files older than retention period
├── analysis/
│   ├── ranking.py           # Rank markets by return potential
│   ├── news.py              # NewsAPI query for top markets
│   └── sentiment.py         # LLM sentiment analysis (pluggable backend)
├── dashboard/
│   ├── app.py               # FastAPI dashboard server
│   ├── templates/
│   │   └── index.html       # Dashboard UI
│   └── static/
├── scripts/
│   ├── run_ingest.py        # CLI: run one ingestion cycle
│   ├── run_analysis.py      # CLI: run analysis pipeline
│   └── run_dashboard.py     # CLI: start dashboard server
└── main.py                  # Full pipeline: ingest → analyze → serve
```

## Quick Start

```bash
# Single ingestion + analysis cycle
python3 platform/main.py

# Start dashboard
python3 platform/scripts/run_dashboard.py

# Run continuous ingestion (configurable interval)
python3 platform/scripts/run_ingest.py --loop

# Cleanup old data
python3 platform/storage/cleanup.py
```

## Data Layout (Parquet)

```
data/
├── polymarket/
│   ├── 2026-02-18/
│   │   ├── 08-00.parquet
│   │   ├── 08-15.parquet
│   │   └── ...
│   └── 2026-02-19/
│       └── ...
├── kalshi/
│   └── (same structure)
├── news/
│   └── (same structure)
└── analysis/
    └── (same structure)
```

## Configuration

Edit `config.yaml` to adjust intervals, retention, API keys, LLM backend, etc.

## AWS Migration Path

- Storage: Parquet → S3 + Athena/Glue
- Ingest: runner.py → Lambda + EventBridge
- Analysis: sentiment.py → Lambda + Bedrock
- Dashboard: FastAPI → ECS/Fargate or Lambda + API Gateway
```
