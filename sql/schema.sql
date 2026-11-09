-- GHC Sentiment Intelligence — PostgreSQL 15 + TimescaleDB schema.
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS assets (
  symbol             TEXT PRIMARY KEY,
  name               TEXT,
  sector             TEXT,
  marketcap          DOUBLE PRECISION,
  circulating_supply DOUBLE PRECISION,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS posts (
  id               BIGSERIAL PRIMARY KEY,
  post_id          TEXT NOT NULL UNIQUE,
  timestamp        TIMESTAMPTZ NOT NULL,
  asset            TEXT NOT NULL,
  source           TEXT NOT NULL,
  author           TEXT,
  followers        INTEGER NOT NULL DEFAULT 0,
  text             TEXT NOT NULL,
  likes            INTEGER NOT NULL DEFAULT 0,
  comments         INTEGER NOT NULL DEFAULT 0,
  shares           INTEGER NOT NULL DEFAULT 0,
  sentiment        DOUBLE PRECISION NOT NULL DEFAULT 0,
  sentiment_label  TEXT NOT NULL DEFAULT 'neutral',
  influence_score  DOUBLE PRECISION NOT NULL DEFAULT 0,
  engagement_score DOUBLE PRECISION NOT NULL DEFAULT 0,
  is_bot           BOOLEAN NOT NULL DEFAULT FALSE,
  narrative        TEXT,
  language         TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
SELECT create_hypertable('posts', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_posts_asset_ts ON posts (asset, timestamp DESC);

CREATE TABLE IF NOT EXISTS news (
  id        BIGSERIAL PRIMARY KEY,
  headline  TEXT NOT NULL,
  source    TEXT NOT NULL,
  url       TEXT,
  asset     TEXT,
  sentiment DOUBLE PRECISION NOT NULL DEFAULT 0,
  timestamp TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('news', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_news_asset_ts ON news (asset, timestamp DESC);

CREATE TABLE IF NOT EXISTS whale_activity (
  id        BIGSERIAL PRIMARY KEY,
  wallet    TEXT NOT NULL,
  asset     TEXT NOT NULL,
  value_usd DOUBLE PRECISION NOT NULL,
  action    TEXT NOT NULL,
  direction TEXT,
  source    TEXT,
  timestamp TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('whale_activity', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_whale_asset_ts ON whale_activity (asset, timestamp DESC);

CREATE TABLE IF NOT EXISTS market_metrics (
  id              BIGSERIAL PRIMARY KEY,
  asset           TEXT NOT NULL,
  price           DOUBLE PRECISION NOT NULL,
  volume          DOUBLE PRECISION NOT NULL,
  open_interest   DOUBLE PRECISION,
  funding_rate    DOUBLE PRECISION,
  liquidations    DOUBLE PRECISION,
  timestamp       TIMESTAMPTZ NOT NULL
);
SELECT create_hypertable('market_metrics', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_metrics_asset_ts ON market_metrics (asset, timestamp DESC);

CREATE TABLE IF NOT EXISTS signals (
  id                BIGSERIAL PRIMARY KEY,
  asset             TEXT NOT NULL,
  alpha_score       DOUBLE PRECISION NOT NULL,
  sentiment_score   DOUBLE PRECISION NOT NULL,
  attention_score   DOUBLE PRECISION NOT NULL,
  velocity_score    DOUBLE PRECISION NOT NULL,
  smart_money_score DOUBLE PRECISION NOT NULL,
  volume_score      DOUBLE PRECISION NOT NULL,
  confidence        DOUBLE PRECISION NOT NULL DEFAULT 0,
  reliability       DOUBLE PRECISION NOT NULL DEFAULT 0,
  classification    TEXT NOT NULL,
  explanation       JSONB NOT NULL DEFAULT '{}'::jsonb,
  timestamp         TIMESTAMPTZ NOT NULL DEFAULT now()
);
SELECT create_hypertable('signals', 'timestamp', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS ix_signals_asset_ts ON signals (asset, timestamp DESC);

CREATE TABLE IF NOT EXISTS alerts (
  id              BIGSERIAL PRIMARY KEY,
  asset           TEXT NOT NULL,
  kind            TEXT NOT NULL,
  reason          TEXT NOT NULL,
  confidence      DOUBLE PRECISION NOT NULL,
  expected_impact TEXT NOT NULL,
  payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_alerts_asset_ts ON alerts (asset, created_at DESC);

CREATE TABLE IF NOT EXISTS trades (
  id            BIGSERIAL PRIMARY KEY,
  basket        TEXT NOT NULL,
  symbol        TEXT NOT NULL,
  side          TEXT NOT NULL,
  size_usd      DOUBLE PRECISION NOT NULL,
  entry_price   DOUBLE PRECISION NOT NULL,
  deviation_pct DOUBLE PRECISION NOT NULL DEFAULT 0,
  pnl_usd       DOUBLE PRECISION NOT NULL DEFAULT 0,
  pnl_pct       DOUBLE PRECISION NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'open',
  is_outlier    BOOLEAN NOT NULL DEFAULT FALSE,
  opened_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_trades_basket ON trades (basket, status);

CREATE TABLE IF NOT EXISTS ghc_state (
  id                 INTEGER PRIMARY KEY DEFAULT 1,
  balance_line       DOUBLE PRECISION NOT NULL DEFAULT 0,
  deviation_pct      DOUBLE PRECISION NOT NULL DEFAULT 0,
  zone               TEXT NOT NULL DEFAULT 'between',
  daily_pnl_forecast DOUBLE PRECISION NOT NULL DEFAULT 0,
  csi                DOUBLE PRECISION NOT NULL DEFAULT 0,
  cri_olr            DOUBLE PRECISION NOT NULL DEFAULT 0,
  cri_brc            DOUBLE PRECISION NOT NULL DEFAULT 0,
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS playbook_events (
  id         BIGSERIAL PRIMARY KEY,
  zone       TEXT NOT NULL,
  action     TEXT NOT NULL,
  detail     TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE MATERIALIZED VIEW IF NOT EXISTS mentions_hourly
WITH (timescaledb.continuous) AS
SELECT asset, time_bucket('1 hour', timestamp) AS bucket, count(*) AS mentions,
       avg(sentiment) AS avg_sentiment
FROM posts GROUP BY asset, bucket;

SELECT add_retention_policy('mentions_hourly', INTERVAL '90 days');
