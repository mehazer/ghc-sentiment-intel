"""Feature construction for forward-return prediction."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import MarketMetric, Signal, WhaleActivity

FEATURES = [
    "sentiment", "agi", "velocity", "smart_money", "volume_change",
    "funding_rate", "open_interest_change", "whale_net_usd", "mention_count",
]
HORIZONS = {6: "ret_6h", 12: "ret_12h", 24: "ret_24h", 72: "ret_72h"}


def build_dataset(db: Session, asset: str, lookback_days: int = 180) -> pd.DataFrame:
    """Assemble an hourly feature frame and forward returns.

    Signals are the truth source for sentiment/attention/smart-money so the model
    learns exactly what production sees. Rows missing a horizon are dropped.
    """
    since = datetime.now(tz=UTC) - timedelta(days=lookback_days)
    metrics = db.scalars(
        select(MarketMetric).where(MarketMetric.asset == asset.upper(), MarketMetric.timestamp >= since)
        .order_by(MarketMetric.timestamp)
    ).all()
    if not metrics:
        return pd.DataFrame(columns=["timestamp", *FEATURES, *HORIZONS.values()])

    frame = pd.DataFrame([{
        "timestamp": m.timestamp, "price": m.price, "volume": m.volume,
        "open_interest": m.open_interest or 0.0, "funding_rate": m.funding_rate or 0.0,
    } for m in metrics]).set_index("timestamp").sort_index()

    for hours, col in HORIZONS.items():
        frame[col] = frame["price"].shift(-hours) / frame["price"] - 1

    frame["volume_change"] = frame["volume"].pct_change().fillna(0) * 100
    frame["open_interest_change"] = frame["open_interest"].pct_change().fillna(0) * 100

    signals = db.scalars(
        select(Signal).where(Signal.asset == asset.upper(), Signal.timestamp >= since)
        .order_by(Signal.timestamp)
    ).all()
    if signals:
        sig = pd.DataFrame([{
            "timestamp": s.timestamp, "sentiment": s.sentiment_score / 50 - 1,
            "smart_money": s.smart_money_score, "velocity": s.velocity_score,
            "agi": (s.explanation or {}).get("attention_detail", {}).get("agi", 0.0),
            "mention_count": (s.explanation or {}).get("attention_detail", {}).get("mentions_current", 0),
        } for s in signals]).set_index("timestamp").sort_index()
        frame = frame.join(sig, how="left").ffill()
    else:
        for col in ["sentiment", "smart_money", "velocity", "agi", "mention_count"]:
            frame[col] = 0.0

    whales = db.scalars(select(WhaleActivity).where(WhaleActivity.asset == asset.upper(),
                                                   WhaleActivity.timestamp >= since)).all()
    net = 0.0
    for w in whales:
        net += w.value_usd if w.action in {"accumulation", "exchange_outflow"} else -w.value_usd
    frame["whale_net_usd"] = net / max(1, len(frame))

    frame = frame.dropna(subset=list(HORIZONS.values()))
    return frame.reset_index()[["timestamp", *FEATURES, *HORIZONS.values()]]


def time_series_split(frame: pd.DataFrame, test_fraction: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chronological split — never shuffle time series data."""
    cut = int(len(frame) * (1 - test_fraction))
    return frame.iloc[:cut], frame.iloc[cut:]
