"""Pydantic request/response models."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostIn(BaseModel):
    post_id: str
    timestamp: datetime
    asset: str
    source: str
    author: str | None = None
    followers: int = 0
    text: str
    likes: int = 0
    comments: int = 0
    shares: int = 0
    verified: bool = False
    account_age_days: int = 3650


class PostOut(PostIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sentiment: float
    sentiment_label: str
    influence_score: float
    engagement_score: float
    narrative: str | None = None
    language: str | None = None
    is_bot: bool = False


class MarketMetricIn(BaseModel):
    asset: str
    price: float
    volume: float
    open_interest: float | None = None
    funding_rate: float | None = None
    liquidations: float | None = None
    timestamp: datetime


class WhaleIn(BaseModel):
    wallet: str
    asset: str
    value_usd: float
    action: str
    direction: str | None = None
    source: str | None = None
    timestamp: datetime


class NewsIn(BaseModel):
    headline: str
    source: str
    url: str | None = None
    asset: str | None = None
    timestamp: datetime


class ScoreOut(BaseModel):
    asset: str
    timestamp: datetime | None = None
    alpha_score: float
    sentiment_score: float
    attention_score: float
    velocity_score: float
    smart_money_score: float
    volume_score: float
    confidence: float
    reliability: float
    classification: str
    explanation: dict = Field(default_factory=dict)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset: str
    kind: str
    reason: str
    confidence: float
    expected_impact: str
    created_at: datetime


class TradeIn(BaseModel):
    basket: str
    symbol: str
    side: str
    size_usd: float
    entry_price: float
    deviation_pct: float = 0.0


class TradeOut(TradeIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    pnl_usd: float
    pnl_pct: float
    status: str
    is_outlier: bool
    opened_at: datetime
    closed_at: datetime | None = None


class BalanceIn(BaseModel):
    balance_line: float
    current_equity: float
    daily_pnl_forecast: float = 0.0
    csi: float = 0.0
    cri_olr: float = 0.0
    cri_brc: float = 0.0


class GHCStateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    balance_line: float
    deviation_pct: float
    zone: str
    daily_pnl_forecast: float
    csi: float
    cri_olr: float
    cri_brc: float
    updated_at: datetime


class PlaybookOut(BaseModel):
    zone: str
    deviation_pct: float
    actions: list[str]
    guards: list[str]
    updated_at: datetime
