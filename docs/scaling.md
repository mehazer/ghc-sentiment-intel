# Scaling guide

## Current shape

One API process handles ~200 req/s for scoring on commodity hardware because
each request touches a bounded window (30 days of posts, 48 metric rows, whale
aggregates). The heavy work is ingestion volume, not scoring.

## Where it breaks first

| Symptom | Cause | Fix |
|---|---|---|
| Ranking slow (>500 ms) | reading 2 000 signal rows per request | add `signals_latest` materialized view, refresh per cycle |
| Attention queries slow | scanning raw posts | use the `mentions_hourly` continuous aggregate |
| Ingestion falling behind | one scheduler, sequential connectors | shard by asset group across workers |
| DB write saturation | per-row inserts | batch 500–1 000 rows per transaction |
| Memory growth | FinBERT loaded per worker | one model server (Triton/TEI), API calls it |

## Horizontal plan

1. **API** — stateless; scale replicas behind a load balancer. Cache
   `GET /signals/ranking` in Redis for 30 s.
2. **Ingestion** — partition assets across workers (e.g. hash(symbol) % N).
   Enforce idempotency with the unique `post_id`; use `ON CONFLICT DO NOTHING`.
3. **Streaming** — replace polling with Kafka: `raw.posts`, `raw.market`,
   `raw.whales` → enrichment consumers → `signals.computed`. Timescale
   compression on chunks older than 7 days.
4. **Storage** — compress chunks (`ALTER TABLE posts SET (timescaledb.compress)`),
   retention policies per table, tier cold data to object storage.
5. **ML** — train offline on a read replica; serve predictions through a small
   FastAPI service or precompute hourly and store in `signals`.

## Capacity targets

| Stage | Assets | Posts/day | Recommended |
|---|---|---|---|
| Pilot | 20 | 100k | 1 API, 1 ingest, 2 vCPU DB |
| Growth | 200 | 2M | 3 API, 4 ingest, 8 vCPU DB + read replica |
| Scale | 2 000 | 20M | 10 API, Kafka, 16 vCPU DB, compressed chunks, Redis cache |

## Cost control

- Compress and retain raw posts for 180 days; keep aggregates forever.
- Run FinBERT only on posts above an engagement threshold; lexicon handles the
  long tail.
- Batch whale and on-chain polling hourly rather than per event.
