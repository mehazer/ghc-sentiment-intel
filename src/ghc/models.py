"""ORM models: posts, news, whales, market metrics, signals, alerts, trades."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(tz=UTC)


class Asset(Base):
    __tablename__ = "assets"

    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(128))
    sector: Mapped[str | None] = mapped_column(String(64))
    marketcap: Mapped[float | None] = mapped_column(Float)
    circulating_supply: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint("post_id", name="uq_posts_post_id"),
        Index("ix_posts_asset_ts", "asset", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(String(128))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    asset: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(32))
    author: Mapped[str | None] = mapped_column(String(128))
    followers: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    sentiment_label: Mapped[str] = mapped_column(String(24), default="neutral")
    influence_score: Mapped[float] = mapped_column(Float, default=0.0)
    engagement_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    narrative: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class News(Base):
    __tablename__ = "news"
    __table_args__ = (Index("ix_news_asset_ts", "asset", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    headline: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64))
    url: Mapped[str | None] = mapped_column(Text)
    asset: Mapped[str | None] = mapped_column(String(32), index=True)
    sentiment: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class WhaleActivity(Base):
    __tablename__ = "whale_activity"
    __table_args__ = (Index("ix_whale_asset_ts", "asset", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    wallet: Mapped[str] = mapped_column(String(128))
    asset: Mapped[str] = mapped_column(String(32), index=True)
    value_usd: Mapped[float] = mapped_column(Float)
    action: Mapped[str] = mapped_column(String(24))
    # accumulation | distribution | exchange_inflow | exchange_outflow
    direction: Mapped[str | None] = mapped_column(String(16))
    source: Mapped[str | None] = mapped_column(String(32))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class MarketMetric(Base):
    __tablename__ = "market_metrics"
    __table_args__ = (Index("ix_metrics_asset_ts", "asset", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset: Mapped[str] = mapped_column(String(32), index=True)
    price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float] = mapped_column(Float)
    open_interest: Mapped[float | None] = mapped_column(Float)
    funding_rate: Mapped[float | None] = mapped_column(Float)
    liquidations: Mapped[float | None] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (Index("ix_signals_asset_ts", "asset", "timestamp"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset: Mapped[str] = mapped_column(String(32), index=True)
    alpha_score: Mapped[float] = mapped_column(Float)
    sentiment_score: Mapped[float] = mapped_column(Float)
    attention_score: Mapped[float] = mapped_column(Float)
    velocity_score: Mapped[float] = mapped_column(Float)
    smart_money_score: Mapped[float] = mapped_column(Float)
    volume_score: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reliability: Mapped[float] = mapped_column(Float, default=0.0)
    classification: Mapped[str] = mapped_column(String(32))
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_asset_ts", "asset", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    expected_impact: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Trade(Base):
    """A GHC basket leg. Deviation is measured against the balance line."""

    __tablename__ = "trades"
    __table_args__ = (Index("ix_trades_basket", "basket", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    basket: Mapped[str] = mapped_column(String(16))  # buy | sell
    symbol: Mapped[str] = mapped_column(String(32))
    side: Mapped[str] = mapped_column(String(8))  # buy | sell
    size_usd: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    deviation_pct: Mapped[float] = mapped_column(Float)
    pnl_usd: Mapped[float] = mapped_column(Float, default=0.0)
    pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(16), default="open")  # open | closed | cropped
    is_outlier: Mapped[bool] = mapped_column(Boolean, default=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GHCState(Base):
    """Singleton snapshot of the current GHC threshold/regime state."""

    __tablename__ = "ghc_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    balance_line: Mapped[float] = mapped_column(Float, default=0.0)
    deviation_pct: Mapped[float] = mapped_column(Float, default=0.0)
    zone: Mapped[str] = mapped_column(String(24), default="between")
    daily_pnl_forecast: Mapped[float] = mapped_column(Float, default=0.0)
    csi: Mapped[float] = mapped_column(Float, default=0.0)
    cri_olr: Mapped[float] = mapped_column(Float, default=0.0)
    cri_brc: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class PlaybookEvent(Base):
    __tablename__ = "playbook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone: Mapped[str] = mapped_column(String(24))
    action: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
