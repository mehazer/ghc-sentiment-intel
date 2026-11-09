"""Assemble engine inputs from stored data and persist a signal."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..engines.alpha import AlphaEngine
from ..engines.attention import AttentionEngine
from ..engines.smart_money import smart_money_snapshot
from ..models import MarketMetric, Post, Signal, WhaleActivity


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def compute_signal(db: Session, asset: str, lookback_days: int = 30) -> Signal:
    asset = asset.upper()
    now = _now()
    since = now - timedelta(days=lookback_days)

    posts = db.scalars(
        select(Post).where(Post.asset == asset, Post.timestamp >= since)
    ).all()
    posts = [p for p in posts if not p.is_bot]
    timestamps = [_aware(p.timestamp) for p in posts]

    # Influence-weighted sentiment; bot and spam posts already excluded.
    weight_sum = sum(max(p.influence_score, 1.0) for p in posts)
    sentiment = (
        sum(p.sentiment * max(p.influence_score, 1.0) for p in posts) / weight_sum
        if weight_sum else 0.0
    )
    attention = AttentionEngine().compute(timestamps, now)
    velocity_score = max(0.0, min(100.0, 50 + attention.acceleration * 4 + attention.velocity * 2))

    metrics = db.scalars(
        select(MarketMetric)
        .where(MarketMetric.asset == asset)
        .order_by(MarketMetric.timestamp.desc())
        .limit(48)
    ).all()
    metrics = list(reversed(metrics))
    price_change = 0.0
    volume_growth = 0.0
    oi_change = 0.0
    funding = 0.0
    if len(metrics) >= 2:
        first, last = metrics[0], metrics[-1]
        price_change = (last.price / first.price - 1) * 100 if first.price else 0.0
        volume_growth = (last.volume / first.volume - 1) * 100 if first.volume else 0.0
        if first.open_interest and last.open_interest:
            oi_change = (last.open_interest / first.open_interest - 1) * 100
    if metrics:
        funding = metrics[-1].funding_rate or 0.0

    whales = db.scalars(select(WhaleActivity).where(
        WhaleActivity.asset == asset, WhaleActivity.timestamp >= since)).all()
    accumulation = sum(w.value_usd for w in whales if w.action in {"accumulation", "exchange_outflow"})
    distribution = sum(w.value_usd for w in whales if w.action in {"distribution", "exchange_inflow"})
    inflow = sum(w.value_usd for w in whales if w.action == "exchange_inflow")
    outflow = sum(w.value_usd for w in whales if w.action == "exchange_outflow")
    sm = smart_money_snapshot(accumulation, distribution, inflow, outflow, oi_change, funding, price_change)

    coverage = min(1.0, (0.4 if posts else 0) + (0.3 if metrics else 0) + (0.3 if whales else 0) + 0.1)
    agreeing = 1.0 if (sentiment > 0.15) == (sm.score > 55) else 0.5

    result = AlphaEngine().score(
        sentiment=sentiment, attention=attention.score, velocity=velocity_score,
        smart_money=sm.score, volume_growth_pct=volume_growth, price_change_pct=price_change,
        data_coverage=coverage, sources_agreeing=agreeing,
    )
    signal = Signal(
        asset=asset, alpha_score=result.alpha_score, sentiment_score=result.sentiment_score,
        attention_score=result.attention_score, velocity_score=result.velocity_score,
        smart_money_score=result.smart_money_score, volume_score=result.volume_score,
        confidence=result.confidence, reliability=result.reliability,
        classification=result.classification,
        explanation={**result.explanation,
                     "attention_detail": attention.__dict__,
                     "smart_money_detail": sm.__dict__},
        timestamp=now,
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal
