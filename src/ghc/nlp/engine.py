"""NLP pipeline: clean → language → sentiment → narrative → influence.

The deterministic lexicon path is always available and is what tests exercise.
A FinBERT/transformers backend can be plugged in without changing callers:
set ``GHC_SENTIMENT_BACKEND=finbert`` and provide a model path.
"""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime

from .narratives import detect_narrative

URL_RE = re.compile(r"https?://\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
EMOJI_RE = re.compile(
    "[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF" "\U0001F1E6-\U0001F1FF" "]+"
)
SPACE_RE = re.compile(r"\s+")
SPAM_RE = re.compile(
    r"(free\s*(crypto|token|giveaway)|airdrop\s*claim|double\s*your|"
    r"join\s*(my|our)\s*(telegram|discord)|dm\s*me\s*(to|for)\s*(earn|profit)|"
    r"guaranteed\s*(profit|returns)|100x\s*guaranteed|click\s*here)",
    re.IGNORECASE,
)

BULLISH = {
    "bullish": 0.8, "moon": 0.7, "pump": 0.6, "breakout": 0.7, "rally": 0.6,
    "accumulate": 0.7, "accumulation": 0.7, "buy": 0.4, "long": 0.4,
    "adoption": 0.5, "partnership": 0.5, "upgrade": 0.5, "approval": 0.6,
    "etf": 0.4, "inflow": 0.5, "support": 0.3, "undervalued": 0.6,
    "surge": 0.7, "soar": 0.7, "ath": 0.7, "all-time high": 0.8, "green": 0.3,
    "buyback": 0.6, "burn": 0.5, "halving": 0.5, "institutional": 0.5,
}
BEARISH = {
    "bearish": -0.8, "dump": -0.7, "crash": -0.8, "sell": -0.4, "short": -0.4,
    "hack": -0.8, "exploit": -0.8, "rug": -0.9, "scam": -0.9, "fraud": -0.8,
    "outflow": -0.5, "liquidation": -0.6, "liquidated": -0.6, "unlock": -0.5,
    "lawsuit": -0.6, "ban": -0.7, "delist": -0.8, "downtrend": -0.7,
    "resistance": -0.3, "overvalued": -0.6, "fud": -0.4, "red": -0.3,
    "bankruptcy": -0.9, "insolvent": -0.9, "fear": -0.5, "capitulation": -0.8,
}
NEGATIONS = {"not", "no", "never", "cannot", "can't", "won't", "isn't", "aren't", "don't", "doesn't"}

LABELS = (
    (0.6, "strong_bullish"),
    (0.15, "bullish"),
    (-0.15, "neutral"),
    (-0.6, "bearish"),
)


def clean_text(text: str) -> str:
    """Normalise social text while keeping sentiment-bearing emoji signals."""
    if not text:
        return ""
    emoji_signal = 0
    for match in EMOJI_RE.findall(text):
        if any(ch in match for ch in "🚀📈🔥💎🟢✅"):
            emoji_signal += 1
        if any(ch in match for ch in "📉🔻💀🩸❌"):
            emoji_signal -= 1
    out = URL_RE.sub(" ", text)
    out = MENTION_RE.sub(" ", out)
    out = HASHTAG_RE.sub(r"\1", out)
    out = EMOJI_RE.sub(" ", out)
    out = SPACE_RE.sub(" ", out).strip()
    if emoji_signal:
        out = f"{out} {'bullish' if emoji_signal > 0 else 'bearish'}"
    return out


def is_spam(text: str) -> bool:
    return bool(SPAM_RE.search(text or ""))


def is_probable_bot(followers: int, following: int,
                    account_age_days: int, posts_per_day: float) -> bool:
    """Heuristic bot filter, deliberately conservative."""
    if account_age_days <= 0:
        return False
    ratio = following / max(followers, 1)
    young_and_hyperactive = account_age_days < 30 and posts_per_day > 40
    follow_farming = ratio > 20 and followers < 200
    return young_and_hyperactive or follow_farming or posts_per_day > 150


def detect_language(text: str) -> str:
    """Script-based detection for the five required languages, English default."""
    cyrillic = len(re.findall(r"[\u0400-\u04FF]", text))
    arabic = len(re.findall(r"[\u0600-\u06FF]", text))
    cjk = len(re.findall(r"[\u4E00-\u9FFF]", text))
    turkish_chars = len(re.findall(r"[ğüşıöçĞÜŞİÖÇ]", text))
    total = max(len(text), 1)
    if cyrillic / total > 0.15:
        return "ru"
    if arabic / total > 0.15:
        return "ar"
    if cjk / total > 0.15:
        return "zh"
    if turkish_chars >= 2:
        return "tr"
    return "en"


def score_sentiment(text: str) -> tuple[float, str]:
    """Lexicon sentiment in [-1, 1] with negation handling."""
    cleaned = clean_text(text).lower()
    if not cleaned:
        return 0.0, "neutral"
    tokens = re.findall(r"[a-z']+", cleaned)
    total = 0.0
    hits = 0
    for i, token in enumerate(tokens):
        value = BULLISH.get(token) or BEARISH.get(token)
        phrase = None
        if token in ("all", "time", "rug", "play"):
            bigram = f"{token} {tokens[i + 1]}" if i + 1 < len(tokens) else ""
            phrase = BULLISH.get(bigram) or BEARISH.get(bigram)
        value = phrase if phrase is not None else value
        if value is None:
            continue
        if i and tokens[i - 1] in NEGATIONS:
            value = -value * 0.8
        total += value
        hits += 1
    if not hits:
        return 0.0, "neutral"
    # Saturating average keeps long posts from dominating short, sharp calls.
    raw = total / math.sqrt(hits + 1)
    score = max(-1.0, min(1.0, raw))
    label = "strong_bearish"
    for threshold, name in LABELS:
        if score >= threshold:
            label = name
            break
    return round(score, 4), label


def influence_score(followers: int, engagement_rate: float,
                    account_age_days: int, verified: bool,
                    historical_accuracy: float) -> float:
    """log10(followers+1) × authority × historical accuracy, normalised to 0-100."""
    reach = math.log10(max(followers, 0) + 1)
    authority = 1.0
    authority += 0.25 if verified else 0.0
    authority += min(0.35, engagement_rate * 2.5)
    authority += min(0.20, max(0.0, account_age_days / 3650) * 0.20)
    accuracy = 0.5 + 0.5 * max(0.0, min(1.0, historical_accuracy))
    raw = reach * authority * accuracy
    return round(min(100.0, raw / 9.0 * 100.0), 2)


def engagement_score(likes: int, comments: int, shares: int, followers: int) -> float:
    interactions = likes + 2 * comments + 3 * shares
    rate = interactions / max(followers, 1)
    return round(min(100.0, math.log10(interactions + 1) * 18 + min(30.0, rate * 300)), 2)


@dataclass
class EnrichedPost:
    post_id: str
    asset: str
    source: str
    timestamp: datetime
    text: str
    sentiment: float
    sentiment_label: str
    influence_score: float
    engagement_score: float
    language: str
    narrative: str | None
    narrative_confidence: float
    is_bot: bool
    is_spam: bool
    meta: dict = field(default_factory=dict)


class NLPEngine:
    """Facade used by ingestion and API. Thread-safe and stateless."""

    def __init__(self, backend: str | None = None) -> None:
        self.backend = backend or os.getenv("GHC_SENTIMENT_BACKEND", "lexicon")
        self._model = None
        if self.backend == "finbert":
            self._model = self._load_finbert()

    @staticmethod
    def _load_finbert():
        try:  # pragma: no cover - optional heavy dependency
            from transformers import pipeline

            path = os.getenv("GHC_FINBERT_MODEL", "ProsusAI/finbert")
            return pipeline("sentiment-analysis", model=path, truncation=True)
        except Exception:  # pragma: no cover
            return None

    def sentiment(self, text: str) -> tuple[float, str]:
        if self._model is not None:  # pragma: no cover
            try:
                result = self._model(text[:512])[0]
                label = result["label"].lower()
                conf = float(result["score"])
                mapping = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}
                base = mapping.get(label, 0.0) * conf
                label_out = "bullish" if base > 0.15 else "bearish" if base < -0.15 else "neutral"
                if conf > 0.85 and base != 0:
                    label_out = f"strong_{label_out}"
                return round(base, 4), label_out
            except Exception:  # pragma: no cover
                pass
        return score_sentiment(text)

    def enrich(self, post) -> EnrichedPost:
        cleaned = clean_text(post.text)
        language = detect_language(post.text)
        sentiment, label = self.sentiment(post.text)
        narrative, nconf = detect_narrative(cleaned)
        eng = engagement_score(post.likes, post.comments, post.shares, post.followers)
        rate = eng / 100.0
        accuracy = getattr(post, "historical_accuracy", 0.5)
        inf = influence_score(
            post.followers, rate, getattr(post, "account_age_days", 3650),
            getattr(post, "verified", False), accuracy,
        )
        return EnrichedPost(
            post_id=post.post_id,
            asset=post.asset.upper(),
            source=post.source,
            timestamp=post.timestamp,
            text=cleaned,
            sentiment=sentiment,
            sentiment_label=label,
            influence_score=inf,
            engagement_score=eng,
            language=language,
            narrative=narrative,
            narrative_confidence=nconf,
            is_bot=is_probable_bot(
                post.followers, getattr(post, "following", 0),
                getattr(post, "account_age_days", 3650), getattr(post, "posts_per_day", 0.0),
            ),
            is_spam=is_spam(post.text),
        )
