"""Composite Risk Indicator: overall liquidation risk and per-basket contribution."""
from __future__ import annotations

from .models import RiskReport


def overall_liquidation_risk(deviation_pct: float, outlier_ratio: float, leverage: float,
                             funding_rate: float, daily_pnl_forecast_pct: float) -> tuple[float, list[str]]:
    """0-100, higher means closer to forced de-risking."""
    drivers: list[str] = []
    band = min(100.0, abs(deviation_pct) / 2.0)  # 200% deviation = maxed
    if abs(deviation_pct) > 100:
        drivers.append(f"deviation {deviation_pct:.0f}% beyond the outer threshold")
    outl = min(100.0, outlier_ratio * 250)
    if outlier_ratio > 0.2:
        drivers.append(f"{outlier_ratio:.0%} of open trades are outliers")
    lev = min(100.0, max(0.0, (leverage - 1) * 12.5))  # 1x = 0, 9x = 100
    if leverage > 5:
        drivers.append(f"leverage {leverage:.1f}x")
    fund = min(100.0, abs(funding_rate) / 0.001 * 100)
    if abs(funding_rate) > 0.0005:
        drivers.append(f"funding {funding_rate:.4%} is extreme")
    pnl = min(100.0, max(0.0, -daily_pnl_forecast_pct * 20))
    if daily_pnl_forecast_pct < 0:
        drivers.append(f"daily PnL forecast {daily_pnl_forecast_pct:.2f}%")

    olr = 0.30 * band + 0.25 * outl + 0.20 * lev + 0.10 * fund + 0.15 * pnl
    return round(min(100.0, olr), 2), drivers


def basket_risk_contribution(exposure: dict[str, float],
                             outlier_counts: dict[str, float] | None = None) -> dict[str, float]:
    """Share of total risk by basket, weighting outlier density 2x."""
    outlier_counts = outlier_counts or {}
    weighted = {k: max(0.0, v) * (1 + 2 * outlier_counts.get(k, 0.0))
                for k, v in exposure.items()}
    total = sum(weighted.values())
    if total <= 0:
        return dict.fromkeys(exposure, 0.0)
    return {k: round(v / total * 100, 2) for k, v in weighted.items()}


def build_risk_report(**kwargs) -> RiskReport:
    olr, drivers = overall_liquidation_risk(**{k: v for k, v in kwargs.items()
                                               if k in {"deviation_pct", "outlier_ratio", "leverage",
                                                        "funding_rate", "daily_pnl_forecast_pct"}})
    brc = basket_risk_contribution(kwargs.get("exposure", {}), kwargs.get("outlier_counts"))
    level = "critical" if olr >= 75 else "elevated" if olr >= 50 else "normal"
    return RiskReport(olr=olr, brc=brc, level=level, drivers=drivers)
