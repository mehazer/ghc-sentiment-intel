"""The five-zone GHC playbook, transcribed from the threshold sheet.

Between S1 and B1 you hold and police risk: funding, daily PnL forecast, keep
daily PnL positive, minor adjustments, scan both baskets for candidates.
Above S1 you ladder buy limits, crop outliers, take profit, then re-measure.
Above S2 it escalates to market orders. B1/B2 mirror the same logic.
"""
from __future__ import annotations

from .models import Playbook, Zone

_BASE_GUARDS = [
    "Outlier definition: any trade PnL below the ATH/ATL condition or worse than "
    "the configured PnL threshold.",
    "Daily PnL must stay positive; block new risk if forecast turns negative.",
    "Re-check funding rate before adding exposure.",
]

_SELL_1 = [
    "Set buy limits (buy-basket orders) on the ladder below the balance line.",
    "Crop outliers flagged by GHC-OD.",
    "Take profit on extended legs.",
    "Re-calculate GHC-CSI and GHC thresholds once the orders are filled.",
    "Adjust closer orders to the new levels.",
]

_SELL_2 = [
    "Set market buy orders — the move is beyond the second threshold.",
    "Crop outliers and take profit in the same pass.",
    "Re-calculate GHC-CSI.",
]

_BUY_1 = [
    "Set sell limits (sell-basket orders) on the ladder above the balance line.",
    "Crop outliers flagged by GHC-OD.",
    "Take profit on extended legs.",
    "Re-calculate GHC-CSI and GHC thresholds once the orders are filled.",
    "Adjust closer orders to the new levels.",
]

_BUY_2 = [
    "Set market sell orders — the move is beyond the second threshold.",
    "Crop outliers and take profit in the same pass.",
    "Re-calculate GHC-CSI.",
]


def playbook_for(zone: Zone) -> Playbook:
    if zone == Zone.BETWEEN:
        return Playbook(
            zone=zone,
            actions=[
                "Check funding rate.",
                "Check daily PnL forecast.",
                "Ensure daily PnL > 0.",
                "Do minor adjustments only.",
                "Check both buy and sell baskets for candidates.",
            ],
            guards=list(_BASE_GUARDS),
            recalc_required=False,
            order_type="limit",
        )
    if zone == Zone.SELL_1:
        return Playbook(zone, list(_SELL_1), list(_BASE_GUARDS), True, "limit")
    if zone == Zone.SELL_2:
        return Playbook(zone, list(_SELL_2), list(_BASE_GUARDS), True, "market")
    if zone == Zone.BUY_1:
        return Playbook(zone, list(_BUY_1), list(_BASE_GUARDS), True, "limit")
    return Playbook(zone, list(_BUY_2), list(_BASE_GUARDS), True, "market")
