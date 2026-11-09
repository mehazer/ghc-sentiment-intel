# Deployment guide

## Docker Compose (single host, production-shaped)

```bash
cp .env.example .env      # set POSTGRES_PASSWORD, GHC_CORS_ORIGINS, tokens
docker compose up --build -d
docker compose ps
```

Services: `db` (TimescaleDB, schema auto-applied), `redis`, `api` (uvicorn,
2 workers, healthcheck), `web` (Next.js standalone), `prometheus`, `grafana`.

- API: http://localhost:8000/docs
- Dashboard: http://localhost:3000
- Prometheus: http://localhost:9090 — Grafana: http://localhost:3001

Seed demo data inside the stack:

```bash
docker compose exec api python scripts/seed_demo.py \
  --db "$GHC_DATABASE_URL"
```

## AWS

1. **Database** — RDS for PostgreSQL 16 is supported, but TimescaleDB is not
   available on RDS. Use Timescale Cloud, or run Postgres on EC2/EKS with the
   TimescaleDB extension.
2. **API** — ECR image from `backend.Dockerfile`, deployed to ECS Fargate (2+
   tasks) or EKS. Put it behind an ALB with TLS. Secrets in AWS Secrets Manager,
   injected as environment variables.
3. **Web** — same pattern with `web/Dockerfile`, or Vercel with
   `NEXT_PUBLIC_API_URL` pointing at the API domain.
4. **Ingestion** — run `ghc-ingest` as a separate ECS service (1 task) so a
   connector failure never affects API latency.
5. **Observability** — CloudWatch for logs, Managed Prometheus + Grafana, or
   ship `/metrics` to an existing Prometheus.

## Azure

- Azure Database for PostgreSQL Flexible Server does not ship TimescaleDB; use a
  Container App with the `timescale/timescaledb` image or Azure VM.
- API and web as Container Apps with managed identity pulling from ACR.
- Key Vault for secrets; Azure Monitor + Managed Grafana for metrics.

## GCP

- Cloud SQL for PostgreSQL lacks TimescaleDB; use a GCE VM or GKE with the
  TimescaleDB image.
- Cloud Run for API and web (min instances 1 to avoid cold starts on the API).
- Secret Manager + Artifact Registry; Cloud Monitoring with the Prometheus
  sidecar.

## Kubernetes notes

- `api` Deployment: 2–6 replicas, HPA on CPU 65%, readiness `/health`.
- `ingest` Deployment: exactly 1 replica — connectors are not distributed-safe.
- `web` Deployment: 2 replicas behind the ingress.
- Migrations: run `psql -f sql/schema.sql` as an init job; the schema is
  idempotent (`IF NOT EXISTS`).

## Configuration

| Variable | Purpose |
|---|---|
| `GHC_DATABASE_URL` | `postgresql+psycopg://user:pass@host:5432/ghc` |
| `GHC_REDIS_URL` | optional cache / rate-limit store |
| `GHC_CORS_ORIGINS` | comma-separated allowed origins |
| `GHC_X_BEARER_TOKEN` | X API bearer token |
| `GHC_CRYPTOPANIC_TOKEN` | CryptoPanic API token |
| `GHC_GLASSNODE_API_KEY`, `GHC_WHALE_ALERT_API_KEY` | on-chain providers |
| `GHC_SENTIMENT_BACKEND` | `lexicon` (default) or `finbert` |
| `GHC_W_*` | alpha weights, must sum to 1.0 |
| `GHC_GHC_S1/S2/B1/B2` | thresholds as % deviation from balance |

## Health and rollback

- Liveness: `GET /health`. Readiness: same endpoint plus a database round-trip.
- Roll back by redeploying the previous image tag; the schema is additive, so no
  down-migration is required for patch releases.
- Keep `POSTGRES_PASSWORD` and provider tokens out of images and logs.
