"""GHC-OD outlier detection.

An outlier is any trade whose PnL falls below the strategy's ATH/ATL condition
or breaches the configured PnL threshold. Ranking by relative PnL keeps the flag
comparable across position sizes.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OutlierFlag:
    trade_id: int
    symbol: str
    basket: str
    pnl_pct: float
    pnl_usd: float
    severity: str
    reason: str


def detect_outliers(trades, threshold_pct: float = -3.0,
                    atl_lookup: dict[str, float] | None = None) -> list[OutlierFlag]:
    flags: list[OutlierFlag] = []
    for t in trades:
        atl = (atl_lookup or {}).get(t.symbol)
        breach = t.pnl_pct <= threshold_pct
        atl_breach = atl is not None and t.pnl_pct < atl
        if not (breach or atl_breach):
            continue
        severity = "critical" if t.pnl_pct <= threshold_pct * 2 else "warning"
        reason = "below PnL threshold" if breach else "below ATL condition"
        if breach and atl_breach:
            reason = "below PnL threshold and ATL condition"
        flags.append(OutlierFlag(
            trade_id=t.id, symbol=t.symbol, basket=t.basket,
            pnl_pct=round(t.pnl_pct, 3), pnl_usd=round(t.pnl_usd, 2),
            severity=severity, reason=reason,
        ))
    flags.sort(key=lambda f: f.pnl_pct)
    return flags


def outlier_ratio(trades) -> float:
    """Share of open trades currently in outlier territory (0-1)."""
    open_trades = [t for t in trades if t.status == "open"]
    if not open_trades:
        return 0.0
    return round(sum(1 for t in open_trades if t.is_outlier) / len(open_trades), 4)
