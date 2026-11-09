"""Narrative detection: keyword layer plus an optional embedding clusterer."""
from __future__ import annotations

from collections import Counter

NARRATIVES: dict[str, tuple[str, ...]] = {
    "etf": ("etf", "spot etf", "sec approval", "blackrock"),
    "meme": ("meme", "doge", "shib", "pepe", "wif", "bonk"),
    "layer2": ("layer 2", "l2", "rollup", "arbitrum", "optimism", "base chain", "zksync"),
    "gamefi": ("gamefi", "play to earn", "p2e", "gaming token", "metaverse"),
    "ai": ("ai token", "artificial intelligence", "ai agent", "depin ai", "singularity"),
    "unlock": ("token unlock", "vesting", "cliff", "supply increase"),
    "hack": ("exploit", "hack", "drained", "bridge attack", "rug pull"),
    "whale": ("whale accumulation", "whale buying", "smart money", "accumulation"),
    "adoption": ("partnership", "integration", "adoption", "mainstream", "institutional"),
    "regulation": ("sec", "lawsuit", "regulation", "ban", "compliance"),
    "restaking": ("restaking", "eigenlayer", "lrt", "liquid restaking"),
    "rwa": ("rwa", "real world asset", "tokenized treasury"),
}


def detect_narrative(text: str, scores: dict[str, float] | None = None) -> tuple[str | None, float]:
    """Return the best narrative and a 0-1 confidence.

    Keyword hits are the deterministic baseline. If a topic-model score map is
    supplied (BERTopic in production), it is blended in so new narratives can
    surface without a code change.
    """
    low = text.lower()
    hits: Counter[str] = Counter()
    for name, keywords in NARRATIVES.items():
        for kw in keywords:
            if kw in low:
                hits[name] += 2 if " " in kw else 1
    best, best_hits = (None, 0)
    if hits:
        best, best_hits = hits.most_common(1)[0]
    if scores:
        model_best = max(scores, key=scores.get)
        if scores[model_best] > 0.55 and (best is None or scores[model_best] > 0.65):
            return model_best, float(scores[model_best])
    if best is None:
        return None, 0.0
    confidence = min(1.0, 0.35 + 0.15 * best_hits)
    return best, round(confidence, 3)
