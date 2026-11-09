from types import SimpleNamespace

import pytest

from ghc.ghc import build_candidate, decision_indicator, detect_outliers, outlier_ratio
from ghc.ghc.models import Side
from ghc.ghc.risk import basket_risk_contribution, overall_liquidation_risk


def test_candidate_requires_alignment_and_target():
    c = build_candidate("BTC", Side.BUY, alpha_score=90, smart_money=85, sentiment=0.7,
                        price=100, target=105, min_alignment=60)
    assert c is not None and c.side is Side.BUY
    blocked = build_candidate("BTC", Side.BUY, alpha_score=90, smart_money=85, sentiment=0.7,
                              price=110, target=105, min_alignment=60)
    assert blocked is None


def test_sell_side_alignment_inverts():
    c = build_candidate("ETH", Side.SELL, alpha_score=10, smart_money=15, sentiment=-0.8,
                        price=110, target=100, min_alignment=60)
    assert c is not None


def test_decision_indicator_scales_with_quality():
    weak = build_candidate("A", Side.BUY, 51, 50, 0.0, 1, 1, min_alignment=0)
    strong = build_candidate("A", Side.BUY, 95, 90, 0.9, 1, 1, min_alignment=0)
    assert decision_indicator([strong], Side.BUY).score > decision_indicator([weak], Side.BUY).score


def _trade(i, pnl, status="open", basket="buy"):
    return SimpleNamespace(id=i, symbol="BTC", basket=basket, pnl_pct=pnl, pnl_usd=pnl * 10, status=status,
                           is_outlier=pnl <= -3)


def test_outliers_flag_and_sort():
    flags = detect_outliers([_trade(1, -1), _trade(2, -5), _trade(3, -12)], threshold_pct=-3)
    assert [f.trade_id for f in flags] == [3, 2]
    assert flags[0].severity == "critical"


def test_outlier_ratio_ignores_closed():
    trades = [_trade(1, -5), _trade(2, 1), _trade(3, -9, status="closed")]
    assert outlier_ratio(trades) == pytest.approx(0.5)


def test_basket_risk_contribution_sums_to_100():
    brc = basket_risk_contribution({"buy": 60, "sell": 40}, {"buy": 0.2})
    assert sum(brc.values()) == pytest.approx(100, abs=0.1)
    assert brc["buy"] > 60


def test_overall_risk_increases_with_leverage():
    low, _ = overall_liquidation_risk(10, 0.0, 1.0, 0.0, 1.0)
    high, drivers = overall_liquidation_risk(180, 0.5, 9.0, 0.002, -2.0)
    assert high > low > 0
    assert drivers


def test_rank_candidates_orders_by_alignment():
    from ghc.ghc import rank_candidates

    rows = [
        {"symbol": "A", "alpha_score": 50, "smart_money": 50, "sentiment": 0.0},
        {"symbol": "B", "alpha_score": 92, "smart_money": 88, "sentiment": 0.8},
        {"symbol": "C", "alpha_score": 75, "smart_money": 70, "sentiment": 0.4},
    ]
    ranked = rank_candidates(rows, Side.BUY)
    assert [c.symbol for c in ranked] == ["B", "C", "A"]
    assert ranked[0].confidence > ranked[-1].confidence


def test_rank_candidates_respects_min_alignment():
    from ghc.ghc import rank_candidates

    bearish = [{"symbol": "A", "alpha_score": 20, "smart_money": 20, "sentiment": -0.6}]
    bullish = [{"symbol": "B", "alpha_score": 90, "smart_money": 85, "sentiment": 0.7}]
    # A bearish book aligns with the sell side, not the buy side.
    assert rank_candidates(bearish, Side.BUY, min_alignment=60) == []
    assert rank_candidates(bearish, Side.SELL, min_alignment=60)
    assert rank_candidates(bullish, Side.SELL, min_alignment=60) == []
