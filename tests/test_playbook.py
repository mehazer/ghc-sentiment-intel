from ghc.ghc import playbook_for
from ghc.ghc.models import Zone


def test_between_zone_holds_and_polices_risk():
    pb = playbook_for(Zone.BETWEEN)
    joined = " ".join(pb.actions).lower()
    assert "funding" in joined and "daily pnl" in joined
    assert pb.order_type == "limit"
    assert pb.recalc_required is False


def test_sell_1_ladders_buy_limits_and_recalcs():
    pb = playbook_for(Zone.SELL_1)
    joined = " ".join(pb.actions).lower()
    assert "buy limits" in joined
    assert "crop outliers" in joined
    assert pb.recalc_required


def test_sell_2_escalates_to_market_orders():
    pb = playbook_for(Zone.SELL_2)
    assert pb.order_type == "market"
    assert any("market buy" in a.lower() for a in pb.actions)


def test_buy_side_mirrors_sell_side():
    s1 = playbook_for(Zone.SELL_1)
    b1 = playbook_for(Zone.BUY_1)
    assert len(s1.actions) == len(b1.actions)
    assert "sell limits" in " ".join(b1.actions).lower()
    assert playbook_for(Zone.BUY_2).order_type == "market"
