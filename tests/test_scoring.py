import pytest

from ghc.engines.alpha import AlphaEngine, classify_alpha


def test_weights_normalise():
    engine = AlphaEngine({"sentiment": 1, "attention": 1, "velocity": 1, "smart_money": 1, "volume": 1})
    assert sum(engine.weights.values()) == pytest.approx(1.0)


def test_perfect_inputs_score_high():
    result = AlphaEngine().score(sentiment=1.0, attention=100, velocity=100,
                                 smart_money=100, volume_growth_pct=80, price_change_pct=5)
    assert result.alpha_score == pytest.approx(100, abs=0.5)
    assert result.classification == "Exceptional Opportunity"


def test_negative_sentiment_drags_score():
    good = AlphaEngine().score(sentiment=0.8, attention=70, velocity=60, smart_money=70)
    bad = AlphaEngine().score(sentiment=-0.8, attention=70, velocity=60, smart_money=70)
    assert good.alpha_score > bad.alpha_score + 20


def test_explanation_identifies_driver():
    result = AlphaEngine().score(sentiment=0.5, attention=95, velocity=20, smart_money=50)
    assert result.explanation["primary_driver"] == "attention"
    assert "summary" in result.explanation


def test_classification_bands():
    assert classify_alpha(90) == "Exceptional Opportunity"
    assert classify_alpha(75) == "Strong Opportunity"
    assert classify_alpha(60) == "Bullish"
    assert classify_alpha(30) == "Neutral"
    assert classify_alpha(10) == "Very Bearish"


def test_confidence_rewards_coverage():
    low = AlphaEngine().score(0.2, 50, 50, 50, data_coverage=0.1, sources_agreeing=0.2)
    high = AlphaEngine().score(0.2, 50, 50, 50, data_coverage=1.0, sources_agreeing=1.0)
    assert high.confidence > low.confidence
    assert high.reliability > low.reliability


def test_diff_explains_change():
    engine = AlphaEngine()
    a = engine.score(0.1, 40, 40, 40)
    b = engine.score(0.1, 95, 40, 40)
    d = engine.diff(a, b)
    assert d["driver"] == "attention"
    assert d["delta"] > 0
