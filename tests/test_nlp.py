from datetime import UTC, datetime

import pytest

from ghc.nlp.engine import (
    NLPEngine,
    clean_text,
    detect_language,
    engagement_score,
    influence_score,
    is_probable_bot,
    is_spam,
    score_sentiment,
)
from ghc.nlp.narratives import detect_narrative


def test_cleaning_strips_links_mentions_keeps_signal():
    out = clean_text("Check https://x.com/a @alice $BTC #bullish 🚀")
    assert "http" not in out and "@alice" not in out
    assert "bullish" in out.lower()


def test_sentiment_polarity():
    assert score_sentiment("BTC breakout, whales accumulating")[0] > 0.4
    assert score_sentiment("Bridge hack, price dump incoming")[0] < -0.4
    assert score_sentiment("the market exists") == (0.0, "neutral")


def test_negation_flips_sentiment():
    positive = score_sentiment("this is bullish")[0]
    negated = score_sentiment("this is not bullish")[0]
    assert negated < positive


@pytest.mark.parametrize("text,lang", [
    ("биткоин растет", "ru"),
    ("بيتكوين يرتفع", "ar"),
    ("比特币上涨", "zh"),
    ("piyasa güçlü şimdi", "tr"),
    ("bitcoin is up", "en"),
])
def test_language_detection(text, lang):
    assert detect_language(text) == lang


def test_spam_and_bot_detection():
    assert is_spam("FREE CRYPTO GIVEAWAY click here")
    assert not is_spam("BTC funding normalised today")
    assert is_probable_bot(followers=10, following=5000, account_age_days=5, posts_per_day=200)
    assert not is_probable_bot(followers=20000, following=300, account_age_days=2000, posts_per_day=5)


def test_influence_monotonic_in_followers():
    small = influence_score(1_000, 0.01, 1000, False, 0.5)
    large = influence_score(1_000_000, 0.01, 1000, True, 0.8)
    assert large > small


def test_engagement_score_scales():
    assert engagement_score(0, 0, 0, 1000) == 0
    assert engagement_score(1000, 200, 300, 10000) > engagement_score(10, 2, 3, 10000)


def test_narrative_detection():
    name, conf = detect_narrative("Spot ETF approval likely for this asset")
    assert name == "etf" and conf > 0
    assert detect_narrative("nothing to see here")[0] is None


def test_enrich_populates_all_fields():
    class P:
        post_id = "1"
        asset = "btc"
        source = "x"
        text = "whale accumulation 🚀"
        followers = 50000
        likes = 400
        comments = 30
        shares = 90
        verified = True
        account_age_days = 2000
        timestamp = datetime.now(UTC)
    out = NLPEngine(backend="lexicon").enrich(P())
    assert out.asset == "BTC"
    assert out.sentiment > 0
    assert out.influence_score > 0
    assert out.narrative == "whale"
