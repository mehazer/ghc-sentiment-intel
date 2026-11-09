"""Value objects for the GHC (Gradual Hedge Cropping) trading layer."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Zone(str, Enum):
    SELL_2 = "sell_2"      # at/above S2
    SELL_1 = "sell_1"      # at/above S1, below S2
    BETWEEN = "between"    # between B1 and S1
    BUY_1 = "buy_1"        # at/below B1, above B2
    BUY_2 = "buy_2"        # at/below B2


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass
class Levels:
    """Price/equity levels derived from the balance line and deviation bands."""

    balance: float
    s1: float
    s2: float
    b1: float
    b2: float

    def as_dict(self) -> dict[str, float]:
        return {"balance": self.balance, "s1": self.s1, "s2": self.s2, "b1": self.b1, "b2": self.b2}


@dataclass
class ZoneResult:
    zone: Zone
    deviation_pct: float
    level: float
    levels: Levels
    distance_to_next_pct: float | None = None


@dataclass
class Playbook:
    zone: Zone
    actions: list[str]
    guards: list[str]
    recalc_required: bool = False
    order_type: str = "none"


@dataclass
class Candidate:
    symbol: str
    side: Side
    confidence: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class DecisionIndicator:
    label: str
    score: float           # 0-100 confidence in the label
    alignment: float       # strategy alignment, 0-100
    components: dict[str, float] = field(default_factory=dict)


@dataclass
class RiskReport:
    olr: float                      # overall liquidation risk 0-100
    brc: dict[str, float]           # basket risk contribution, sums to 100
    level: str
    drivers: list[str] = field(default_factory=list)
