# Architecture

## Components

| Layer | Responsibility | Code |
|---|---|---|
| Collection | Pull posts, news, whales, prices with bounded retries | `src/ghc/ingestion/` |
| Storage | Time-series and relational persistence | `src/ghc/models.py`, `sql/schema.sql` |
| NLP | Clean, detect language, score sentiment, tag narratives | `src/ghc/nlp/` |
| Engines | Attention, smart money, alpha, alerts | `src/ghc/engines/` |
| GHC | Thresholds, playbook, candidates, outliers, risk | `src/ghc/ghc/` |
| API | FastAPI routers | `src/ghc/api/` |
| UI | Next.js dashboard | `web/` |
| ML | Forward-return models | `src/ghc/ml/` |

## Data flow

1. A connector fetches raw records, retrying with exponential backoff and jitter.
2. Ingestion endpoints enrich each post: spam and bot filters, cleaning, language
   detection, sentiment, narrative, influence and engagement scores.
3. Market and whale records are stored raw; scoring happens on read.
4. `POST /api/signals/{asset}/compute` assembles the five subscores from stored
   data and persists a `signals` row with a full explanation object.
5. The alert engine evaluates rule sets over the latest signal.
6. The GHC layer converts the current equity deviation into a zone and returns
   the corresponding playbook, candidate list, outlier flags and risk report.

## ERD

```
assets(symbol PK, name, sector, marketcap, circulating_supply, updated_at)

posts(id PK, post_id UQ, timestamp, asset, source, author, followers, text,
      likes, comments, shares, sentiment, sentiment_label, influence_score,
      engagement_score, is_bot, narrative, language, created_at)

news(id PK, headline, source, url, asset, sentiment, timestamp)

whale_activity(id PK, wallet, asset, value_usd, action, direction, source, timestamp)

market_metrics(id PK, asset, price, volume, open_interest, funding_rate,
               liquidations, timestamp)

signals(id PK, asset, alpha_score, sentiment_score, attention_score,
        velocity_score, smart_money_score, volume_score, confidence,
        reliability, classification, explanation JSONB, timestamp)

alerts(id PK, asset, kind, reason, confidence, expected_impact, payload JSONB, created_at)

trades(id PK, basket, symbol, side, size_usd, entry_price, deviation_pct,
       pnl_usd, pnl_pct, status, is_outlier, opened_at, closed_at)

ghc_state(id PK=1, balance_line, deviation_pct, zone, daily_pnl_forecast,
          csi, cri_olr, cri_brc, updated_at)

playbook_events(id PK, zone, action, detail, created_at)
```

Assets are referenced by `symbol` text rather than a foreign key so historical
rows survive delistings and symbol reuse stays explicit.

## Indexing strategy

| Index | Purpose |
|---|---|
| `posts(asset, timestamp DESC)` | asset timelines and attention windows |
| `posts(post_id)` unique | ingestion idempotency |
| `market_metrics(asset, timestamp DESC)` | latest metrics, volume and OI changes |
| `whale_activity(asset, timestamp DESC)` | flow aggregation per asset |
| `signals(asset, timestamp DESC)` | ranking and "why did it change" |
| `alerts(asset, created_at DESC)` | per-asset alert history |
| `trades(basket, status)` | open exposure by basket |

Time-series tables are hypertables on `timestamp`, so each index is a per-chunk
B-tree. Ranking queries read the newest 2 000 rows and dedupe in Python; once
volume grows, replace with a `signals_latest` materialized view refreshed each
ingestion cycle.

## Partitioning

- Hypertables: `posts`, `news`, `whale_activity`, `market_metrics`, `signals`.
- Chunk interval: 1 day for `posts`/`signals` at high write rates, 7 days for
  `market_metrics`. Tune with `set_chunk_time_interval`.
- Retention: raw social posts 180 days, metrics 2 years, signals 2 years;
  roll-ups persist indefinitely.
- Continuous aggregate `mentions_hourly` (1-hour buckets, 90-day retention)
  serves the 30-day attention baseline without scanning raw posts.

## Performance

- Attention features are computed from a single indexed range scan per asset.
- Sentiment is O(tokens); lexicon path costs microseconds, FinBERT batches.
- Signal assembly loads one 30-day post window, 48 metric rows and the whale
  window per asset — constant work per request.
- Write paths are bulk inserts inside one transaction.
- Heavy ML training runs offline against the same tables, never in the API path.

## Security

- All credentials come from environment variables (`.env` locally, secrets
  manager in production). Nothing is committed.
- CORS is explicit per environment.
- The API is stateless; put it behind TLS and an auth proxy before exposing it.
- No private keys or exchange trading credentials are handled by this service;
  it is read-only intelligence.
