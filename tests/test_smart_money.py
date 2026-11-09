from ghc.engines.smart_money import smart_money_snapshot


def test_accumulation_with_outflows_scores_bullish():
    snap = smart_money_snapshot(accumulation_usd=8e6, distribution_usd=1e6,
                                exchange_outflow_usd=5e6, exchange_inflow_usd=1e6,
                                oi_change_pct=8, funding_rate=0.00005, price_change_pct=3)
    assert snap.score > 70
    assert "whale accumulation" in snap.signals


def test_distribution_with_inflows_scores_bearish():
    snap = smart_money_snapshot(accumulation_usd=1e6, distribution_usd=9e6,
                                exchange_inflow_usd=8e6, exchange_outflow_usd=1e6,
                                oi_change_pct=-5, funding_rate=0.001, price_change_pct=-4)
    assert snap.score < 40


def test_extreme_funding_penalised():
    healthy = smart_money_snapshot(funding_rate=0.0)
    extreme = smart_money_snapshot(funding_rate=0.002)
    assert healthy.funding_score > extreme.funding_score


def test_empty_inputs_are_neutral():
    snap = smart_money_snapshot()
    assert snap.score == 50
