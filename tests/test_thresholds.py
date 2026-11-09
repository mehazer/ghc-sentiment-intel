import pytest

from ghc.ghc import ThresholdConfig, classify
from ghc.ghc.models import Zone


@pytest.fixture()
def cfg():
    return ThresholdConfig(s1_pct=50, s2_pct=100, b1_pct=-50, b2_pct=-90)


def test_levels_are_symmetric(cfg):
    lv = cfg.levels(1000)
    assert lv.s1 == pytest.approx(1500)
    assert lv.s2 == pytest.approx(2000)
    assert lv.b1 == pytest.approx(500)
    assert lv.b2 == pytest.approx(100)


@pytest.mark.parametrize("value,expected", [
    (2000, Zone.SELL_2), (1600, Zone.SELL_1), (1000, Zone.BETWEEN),
    (300, Zone.BUY_1), (50, Zone.BUY_2),
])
def test_zone_classification(cfg, value, expected):
    assert classify(value, 1000, cfg).zone is expected


def test_boundaries_belong_to_the_outer_zone(cfg):
    # Hitting S1 exactly should already trigger the sell playbook.
    assert classify(1500, 1000, cfg).zone is Zone.SELL_1
    assert classify(500, 1000, cfg).zone is Zone.BUY_1
    assert classify(cfg.levels(1000).b2, 1000, cfg).zone is Zone.BUY_2


def test_deviation_is_signed_percentage(cfg):
    assert classify(1250, 1000, cfg).deviation_pct == pytest.approx(25.0)
    assert classify(800, 1000, cfg).deviation_pct == pytest.approx(-20.0)


def test_invalid_configuration_rejected():
    with pytest.raises(ValueError):
        ThresholdConfig(s1_pct=100, s2_pct=50)
    with pytest.raises(ValueError):
        ThresholdConfig(b1_pct=-50, b2_pct=-10)
    with pytest.raises(ValueError):
        ThresholdConfig(b1_pct=-50, b2_pct=-100)


def test_zero_balance_rejected(cfg):
    with pytest.raises(ValueError):
        cfg.levels(0)
