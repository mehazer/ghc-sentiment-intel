# Roadmap

## Near term
- Wire the remaining connectors: Reddit, Telegram, Discord, CryptoPanic,
  Glassnode, Whale Alert, Google Trends (interfaces exist for X, RSS, Binance).
- Add auth (OIDC) and per-user workspaces.
- `signals_latest` materialized view and Redis caching for ranking.

## Medium term
- Kafka streaming ingestion with exactly-once semantics.
- FinBERT fine-tuned on crypto posts, served from a dedicated inference service.
- BERTopic clustering to discover narratives without a keyword list.
- Model registry with time-series cross-validation and drift monitoring.
- Backtesting harness that replays historical signals against GHC thresholds.

## Long term
- Multi-venue derivatives coverage (Bybit, OKX, Deribit) with cross-venue basis.
- Portfolio-level GHC engine: automatic basket construction from candidates.
- On-chain wallet clustering for real smart-money identification.
- Alert delivery to Telegram/Slack/email with escalation rules.
