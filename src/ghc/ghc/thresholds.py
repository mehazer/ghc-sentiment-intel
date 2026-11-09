"""GHC threshold engine.

The balance line is the hedge-neutral reference. ``s1``/``s2`` are the sell-side
levels above it, ``b1``/``b2`` the buy-side levels below it. Deviation is the
signed percentage distance of the reference (equity or price) from balance:

    deviation_pct = (value / balance - 1) * 100

Positive deviation therefore sits on the sell side of the ladder, negative on the
buy side, matching the S2/S1/balance/B1/B2 sketch.
"""
from __future__ import annotations

from .models import Levels, Zone, ZoneResult


class ThresholdConfig:
    def __init__(self, s1_pct: float = 50.0, s2_pct: float = 100.0,
                 b1_pct: float = -50.0, b2_pct: float = -90.0) -> None:
        if not (s2_pct > s1_pct > 0):
            raise ValueError("require s2_pct > s1_pct > 0")
        if not (b2_pct < b1_pct < 0):
            raise ValueError("require b2_pct < b1_pct < 0")
        if b2_pct <= -100:
            raise ValueError("b2_pct must be greater than -100 so the level stays positive")
        self.s1_pct = s1_pct
        self.s2_pct = s2_pct
        self.b1_pct = b1_pct
        self.b2_pct = b2_pct

    def levels(self, balance: float) -> Levels:
        if balance <= 0:
            raise ValueError("balance line must be positive")
        return Levels(
            balance=balance,
            s1=round(balance * (1 + self.s1_pct / 100), 8),
            s2=round(balance * (1 + self.s2_pct / 100), 8),
            b1=round(balance * (1 + self.b1_pct / 100), 8),
            b2=round(balance * (1 + self.b2_pct / 100), 8),
        )


def classify(value: float, balance: float, config: ThresholdConfig | None = None) -> ZoneResult:
    cfg = config or ThresholdConfig()
    levels = cfg.levels(balance)
    deviation = (value / balance - 1) * 100 if balance else 0.0

    if value >= levels.s2:
        zone, nxt = Zone.SELL_2, None
    elif value >= levels.s1:
        zone, nxt = Zone.SELL_1, (levels.s2 / value - 1) * 100
    elif value > levels.b1:
        zone, nxt = Zone.BETWEEN, None
    elif value > levels.b2:
        zone, nxt = Zone.BUY_1, (levels.b2 / value - 1) * 100
    else:
        zone, nxt = Zone.BUY_2, None

    return ZoneResult(
        zone=zone,
        deviation_pct=round(deviation, 3),
        level=value,
        levels=levels,
        distance_to_next_pct=round(nxt, 3) if nxt is not None else None,
    )
