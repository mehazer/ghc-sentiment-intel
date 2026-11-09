# API reference

Base path: `/api`. Interactive docs: `/docs` (Swagger), `/redoc`.

## Ingestion

### `POST /api/ingest/posts`
Body: array of posts.

```json
[{
  "post_id": "1790000000000000000",
  "timestamp": "2026-11-09T12:00:00Z",
  "asset": "BTC",
  "source": "x",
  "author": "someuser",
  "followers": 120000,
  "text": "whale accumulation, breakout soon 🚀",
  "likes": 800, "comments": 60, "shares": 210,
  "verified": true, "account_age_days": 1800
}]
```

Returns the stored posts with `sentiment`, `sentiment_label`,
`influence_score`, `engagement_score`, `narrative`, `language`, `is_bot`.
Spam is silently dropped; duplicate `post_id` values are skipped.

### `POST /api/ingest/market`
Array of `{asset, price, volume, open_interest, funding_rate, liquidations, timestamp}`.

### `POST /api/ingest/whales`
Array of `{wallet, asset, value_usd, action, direction, source, timestamp}`
where `action` ∈ `accumulation | distribution | exchange_inflow | exchange_outflow`.

### `POST /api/ingest/news`
Array of `{headline, source, url, asset, timestamp}`. Sentiment is scored server-side.

## Signals

### `POST /api/signals/{asset}/compute`
Computes and persists a signal. Returns:

```json
{
  "asset": "ETH",
  "alpha_score": 76.65,
  "sentiment_score": 71.4,
  "attention_score": 100.0,
  "velocity_score": 94.0,
  "smart_money_score": 77.4,
  "volume_score": 6.4,
  "confidence": 1.0,
  "reliability": 0.34,
  "classification": "Strong Opportunity",
  "explanation": {
    "components": {"sentiment": 71.4, "attention": 100.0, "...": 0},
    "weighted_contribution": {"sentiment": 21.4, "attention": 25.0},
    "primary_driver": "attention",
    "summary": "attention is the main driver (25.0 pts); volume contributes least (0.6 pts)."
  },
  "timestamp": "2026-11-09T13:40:13Z"
}
```

### `GET /api/signals/ranking?limit=20`
Latest signal per asset, sorted by alpha descending.

### `GET /api/signals/{asset}/history?limit=100`
Chronological signal history.

### `GET /api/signals/{asset}/why`
Delta versus the previous run, the dominant driver and per-component deltas.

## Alerts

### `POST /api/alerts/evaluate/{asset}`
Runs the four rule sets against the latest signal.

### `GET /api/alerts?limit=50`
Alert history, newest first. Each alert carries `reason`, `confidence`,
`expected_impact` and a `payload` snapshot.

| Kind | Trigger |
|---|---|
| `early_accumulation` | AGI > 2.5, smart money > 60, volume growth > 50%, sentiment > 60 |
| `breakout_watch` | positive velocity, rising OI, AGI > 1.5 |
| `fomo_warning` | sentiment > 90, attention > 90, whales selling or funding extreme |
| `possible_top` | attention extreme, whales distributing, momentum slowing |

## GHC

### `POST /api/ghc/balance`
```json
{"balance_line": 250000, "current_equity": 412000,
 "daily_pnl_forecast": 1800, "csi": 78, "cri_olr": 0, "cri_brc": 0}
```
Returns the computed zone and deviation. Records a `playbook_events` row.

### `GET /api/ghc/state`
Current balance line, deviation, zone and risk inputs.

### `GET /api/ghc/playbook`
Zone plus the ordered `actions` and `guards` for that zone.

### `POST /api/ghc/trades`
```json
{"basket": "buy", "symbol": "BTC", "side": "buy",
 "size_usd": 10000, "entry_price": 67000, "deviation_pct": -12}
```

### `POST /api/ghc/trades/{id}/close?exit_price=...`
Books PnL in USD and percent, marks `closed`, re-evaluates outlier status.

### `GET /api/ghc/trades?status=open`

### `GET /api/ghc/outliers`
`{"ratio": 0.33, "flags": [{"trade_id": 3, "pnl_pct": -12.0, "severity": "critical", ...}]}`

### `GET /api/ghc/risk?leverage=3&funding_rate=0.0008`
```json
{"olr": 42.1, "brc": {"buy": 66.7, "sell": 33.3}, "level": "normal", "drivers": ["..."]}
```

### `GET /api/ghc/candidates?limit=10`
Signals mapped to the side implied by the current zone, with alignment scores.

## Ops

- `GET /health` — liveness and environment
- `GET /metrics` — Prometheus exposition (`ghc_http_requests_total`,
  `ghc_http_request_duration_seconds`, `ghc_http_in_flight`)

## Errors

| Code | Meaning |
|---|---|
| 404 | No signals for asset / trade not found |
| 422 | Validation error (Pydantic detail body) |
| 503 | Database unavailable |
