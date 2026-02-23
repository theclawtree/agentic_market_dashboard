# Agentic Predictive Market Dashboard
![CI](https://github.com/theclawtree/agentic_market_dashboard/actions/workflows/ci.yml/badge.svg)
![Security](https://github.com/theclawtree/agentic_market_dashboard/actions/workflows/security.yml/badge.svg)


A look at the dashboard interface showing recent data:
<img width="1436" height="695" alt="Screen Shot 2026-02-22 at 4 59 00 PM" src="https://github.com/user-attachments/assets/70ca49fb-4516-45a8-bfcc-ba9b41470641" />

---------

# Local Operation

- Use uv for package management: [Install UV](https://docs.astral.sh/uv/getting-started/installation/)

- Copy `config.yaml.example` to `config.yaml` and include your personal AI service key and newsapi.org key. 

To run locally open terminal and execute below commands:
```
git clone git@github.com:theclawtree/agentic_market_dashboard.git # Using ssh
cd agentic_market_dashboard/platform
uv run main.py --dashboard
```

---------

# Next Steps
Future Goals Include:
- Cloud platform
- Users
- Bookmarking
- Education section on modeling markets, historical wins, game time strategies
- Agentic selection of opportunities for given users which match their interests
- Real time news analysis
- Real time hot button trading
