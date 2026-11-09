"""Smart Money Score: 40% whale, 20% flow, 20% open interest, 20% funding."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SmartMoneySnapshot:
    whale_score: float
    flow_score: float
    oi_score: float
    funding_score: float
    score: float
    interpretation: str
    signals: list[str] = field(default_factory=list)


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def smart_money_snapshot(
    accumulation_usd: float = 0.0,
    distribution_usd: float = 0.0,
    exchange_inflow_usd: float = 0.0,
    exchange_outflow_usd: float = 0.0,
    oi_change_pct: float = 0.0,
    funding_rate: float | None = None,
    price_change_pct: float = 0.0,
) -> SmartMoneySnapshot:
    """Convert raw flows into a 0-100 score with a human-readable interpretation.

    Exchange outflow is bullish (coins leaving venues), inflow is bearish.
    Falling OI with rising price marks short covering rather than new money.
    """
    whale_total = accumulation_usd + distribution_usd
    if whale_total > 0:
        net = (accumulation_usd - distribution_usd) / whale_total
        whale = _clamp(50 + net * 50)
    else:
        whale = 50.0

    flow_total = exchange_inflow_usd + exchange_outflow_usd
    if flow_total > 0:
        flow = _clamp(50 + ((exchange_outflow_usd - exchange_inflow_usd) / flow_total) * 50)
    else:
        flow = 50.0

    if oi_change_pct > 0:
        oi = _clamp(50 + min(50.0, oi_change_pct * 5))
        if price_change_pct < 0:
            oi = _clamp(oi - 15)  # new shorts, not accumulation
    elif oi_change_pct < 0:
        oi = _clamp(50 + max(-35.0, oi_change_pct * 5))
    else:
        oi = 50.0

    # Funding near zero is healthy; extreme positive means crowded longs.
    if funding_rate is None:
        funding = 50.0
    else:
        abs_funding = abs(funding_rate)
        if abs_funding <= 0.0001:
            funding = 65.0
        elif funding_rate > 0:
            funding = _clamp(65 - (abs_funding - 0.0001) * 60000)
        else:
            funding = _clamp(65 - (abs_funding - 0.0001) * 30000)

    score = 0.4 * whale + 0.2 * flow + 0.2 * oi + 0.2 * funding
    signals: list[str] = []
    if whale >= 65:
        signals.append("whale accumulation")
    elif whale <= 35:
        signals.append("whale distribution")
    if flow >= 60:
        signals.append("exchange outflows")
    elif flow <= 40:
        signals.append("exchange inflows")
    if oi_change_pct > 5:
        signals.append("open interest rising")
    if funding_rate is not None and abs(funding_rate) > 0.0005:
        signals.append("funding extreme")

    if score >= 75:
        interpretation = "Smart money strongly positioned long"
    elif score >= 60:
        interpretation = "Constructive accumulation"
    elif score >= 40:
        interpretation = "Mixed / no clear edge"
    elif score >= 25:
        interpretation = "Distribution pressure"
    else:
        interpretation = "Smart money exiting"
    return SmartMoneySnapshot(
        whale_score=round(whale, 2), flow_score=round(flow, 2), oi_score=round(oi, 2),
        funding_score=round(funding, 2), score=round(score, 2),
        interpretation=interpretation, signals=signals,
    )


class SmartMoneyEngine:
    def compute(self, **kwargs) -> SmartMoneySnapshot:
        return smart_money_snapshot(**kwargs)
