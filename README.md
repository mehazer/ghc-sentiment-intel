# GHC Sentiment Intelligence

Attention, sentiment and smart-money intelligence for **GHC (Gradual Hedge Cropping)**.

The platform turns noisy social, news, on-chain and derivatives data into five
0–100 subscores, a composite **Alpha Score**, and a GHC trading playbook that
tells you what to do at each threshold level.

```
                 ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
  X / Reddit ───▶│              │   │              │   │              │
  Telegram ─────▶│  Ingestion   │──▶│  NLP Engine  │──▶│   Engines    │
  News / RSS ───▶│  (retry,     │   │  clean, lang │   │ attention    │
  Binance ──────▶│   backoff)   │   │  sentiment   │   │ smart money  │
  On-chain ─────▶│              │   │  narrative   │   │ alpha        │
                 └──────────────┘   └──────────────┘   └──────┬───────┘
                                                              │
                          ┌───────────────────────────────────┴────┐
                          ▼                                        ▼
                   ┌──────────────┐                        ┌──────────────┐
                   │  Postgres +  │                        │   FastAPI    │
                   │  TimescaleDB │◀──────────────────────▶│   /api/*     │
                   └──────────────┘                        └──────┬───────┘
                                                                  │
                                            ┌─────────────────────┴──────┐
                                            ▼                            ▼
                                    ┌──────────────┐            ┌──────────────┐
                                    │  Next.js UI  │            │ Alerts/GHC   │
                                    │  dashboard   │            │ playbook     │
                                    └──────────────┘            └──────────────┘
```

## What it answers

1. Which assets are attracting attention?
2. Is that attention accelerating or fading?
3. Is sentiment improving, and is it genuine or bot-driven?
4. Is smart money accumulating or distributing?
5. Is volume confirming the move?
6. Is this early accumulation or late-stage FOMO?
7. Which GHC threshold are we in, and what is the playbook?

## Quick start (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# API (SQLite by default, no services needed)
uvicorn ghc.main:app --reload --app-dir src

# Demo data + scores
python scripts/seed_demo.py

# Dashboard
cd web && npm install && npm run dev
```

Open http://localhost:3000 for the dashboard and http://localhost:8000/docs for
the API. For the full stack:

```bash
cp .env.example .env
docker compose up --build
```

## Scores

| Component | Weight | Source |
|---|---|---|
| Sentiment | 30% | influence-weighted post sentiment, −1…+1 |
| Attention growth (AGI) | 25% | 24h mentions ÷ 30-day daily average |
| Velocity | 15% | mention acceleration |
| Smart money | 20% | 40% whale · 20% flow · 20% OI · 20% funding |
| Volume confirmation | 10% | volume growth, direction-adjusted |

| Alpha | Classification |
|---|---|
| 86–100 | Exceptional Opportunity |
| 71–85 | Strong Opportunity |
| 51–70 | Bullish |
| 26–50 | Neutral |
| 0–25 | Very Bearish |

Every score carries **confidence** (evidence coverage), **reliability** (source
agreement) and an **explanation** naming the primary driver and weighted
contribution of each component.

## GHC playbook

The balance line is the hedge-neutral reference. Deviation is signed:

```
deviation_pct = (equity / balance − 1) × 100
```

| Zone | Trigger | Action |
|---|---|---|
| Above S2 | ≥ +100% | market buy orders, crop outliers, take profit, recalc CSI |
| Between S1–S2 | +50% to +100% | buy limits, crop outliers, take profit, recalc CSI/thresholds, adjust closer orders |
| Between S1–B1 | −50% to +50% | check funding, check daily PnL forecast, keep PnL > 0, minor adjustments, scan both baskets |
| Between B1–B2 | −90% to −50% | sell limits, crop outliers, take profit, recalc CSI/thresholds |
| Below B2 | < −90% | market sell orders, crop outliers, take profit, recalc CSI |

Outlier definition (GHC-OD): any trade whose PnL breaches the ATH/ATL condition
or falls below the configured PnL threshold (default −3%).

## Layout

```
src/ghc/
  api/           FastAPI routers (ingest, signals, alerts, ghc)
  engines/       attention, smart money, alpha, alerts
  ghc/           thresholds, playbook, candidates, outliers, risk
  ingestion/     connectors, retry/backoff, scheduler
  ml/            dataset builder and model comparison
  nlp/           cleaning, language, sentiment, narratives
  services/      signal assembly
  models.py      SQLAlchemy schema
web/             Next.js dashboard
sql/schema.sql   PostgreSQL + TimescaleDB DDL
tests/           54 unit and integration tests
docs/            architecture, API, deployment, scaling
```

## Tests

```bash
pytest -q            # 54 tests
cd web && npx tsc --noEmit && npm run build
```

## Documentation

- [Architecture](docs/architecture.md)
- [API reference](docs/api.md)
- [User manual](docs/user-manual.md)
- [Deployment guide](docs/deployment.md)
- [Scaling guide](docs/scaling.md)
- [Roadmap](docs/roadmap.md)

## Disclaimer

Scores are probabilistic research output, not investment advice. GHC risk rules
(position sizing, daily PnL floor, outlier cropping) always take precedence.
