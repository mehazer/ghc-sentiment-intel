# Folder structure

```
.
├── backend.Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env.example
├── sql/
│   └── schema.sql               PostgreSQL + TimescaleDB DDL
├── src/ghc/
│   ├── main.py                  FastAPI app, CORS, metrics
│   ├── config.py                env-driven settings
│   ├── db.py                    engine, session, init
│   ├── models.py                ORM models
│   ├── schemas.py               Pydantic contracts
│   ├── api/
│   │   ├── router.py            mounts all routers
│   │   ├── ingest.py            posts, market, whales, news
│   │   ├── signals.py           compute, ranking, history, why
│   │   ├── alerts.py            evaluate, history
│   │   └── ghc.py               balance, state, playbook, trades, outliers, risk
│   ├── engines/
│   │   ├── attention.py         AGI, velocity, acceleration, z-score
│   │   ├── smart_money.py       whale/flow/OI/funding blend
│   │   ├── alpha.py             composite score, confidence, explainability
│   │   └── alerts.py            four rule sets
│   ├── ghc/
│   │   ├── models.py            levels, zones, candidates, risk types
│   │   ├── thresholds.py        level derivation and zone classification
│   │   ├── playbook.py          five-zone action plans
│   │   ├── candidates.py        alignment gates and decision indicator
│   │   ├── outliers.py          GHC-OD detection
│   │   └── risk.py              CRI-OLR and CRI-BRC
│   ├── ingestion/
│   │   ├── base.py              retries, backoff, logging
│   │   ├── binance.py           price, volume, funding, OI
│   │   ├── rss.py               CoinDesk, CoinTelegraph, Decrypt
│   │   ├── x.py                 recent search
│   │   └── scheduler.py         sequential bounded loop
│   ├── ml/
│   │   ├── dataset.py           features and forward returns
│   │   └── train.py             model comparison with TSCV
│   ├── nlp/
│   │   ├── engine.py            cleaning, language, sentiment, influence
│   │   └── narratives.py        narrative taxonomy and detection
│   ├── observability/metrics.py Prometheus middleware and /metrics
│   └── services/scoring.py      assembles and persists signals
├── web/
│   ├── app/                     overview, ghc, asset, narratives, smart-money, alerts
│   ├── components/              gauge, ladder, sparkline
│   └── lib/api.ts               typed API client
├── tests/                       54 unit + integration tests
├── scripts/seed_demo.py         realistic demo dataset
└── docs/                        architecture, api, user manual, deployment, scaling, roadmap
```
