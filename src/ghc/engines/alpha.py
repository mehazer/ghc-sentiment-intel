"""Composite Alpha Score with confidence, reliability and explanations."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import get_settings

CLASSES = (
    (86, "Exceptional Opportunity"),
    (71, "Strong Opportunity"),
    (51, "Bullish"),
    (26, "Neutral"),
    (0, "Very Bearish"),
)


def classify_alpha(score: float) -> str:
    for threshold, label in CLASSES:
        if score >= threshold:
            return label
    return "Very Bearish"


@dataclass
class AlphaResult:
    alpha_score: float
    sentiment_score: float
    attention_score: float
    velocity_score: float
    smart_money_score: float
    volume_score: float
    confidence: float
    reliability: float
    classification: str
    explanation: dict = field(default_factory=dict)


def _volume_score(volume_growth_pct: float, price_change_pct: float) -> float:
    """Volume confirmation: growth matters, direction decides the sign."""
    base = 50 + max(-50.0, min(50.0, volume_growth_pct))
    if price_change_pct > 0 and volume_growth_pct > 0:
        base += 10
    elif price_change_pct < 0 and volume_growth_pct > 0:
        base -= 10
    return max(0.0, min(100.0, base))


class AlphaEngine:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        s = get_settings()
        self.weights = weights or {
            "sentiment": s.w_sentiment,
            "attention": s.w_attention,
            "velocity": s.w_velocity,
            "smart_money": s.w_smart_money,
            "volume": s.w_volume,
        }
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def score(
        self,
        sentiment: float,
        attention: float,
        velocity: float,
        smart_money: float,
        volume_growth_pct: float = 0.0,
        price_change_pct: float = 0.0,
        data_coverage: float = 1.0,
        sources_agreeing: float = 1.0,
    ) -> AlphaResult:
        """``sentiment`` is -1..1; every other input is 0..100."""
        sentiment_component = (sentiment + 1) * 50
        volume_component = _volume_score(volume_growth_pct, price_change_pct)
        parts = {
            "sentiment": sentiment_component,
            "attention": attention,
            "velocity": velocity,
            "smart_money": smart_money,
            "volume": volume_component,
        }
        alpha = sum(self.weights[k] * parts[k] for k in parts)

        # Confidence reflects how much evidence we have; reliability how well
        # the sources agree. Neither changes the raw alpha, only trust in it.
        confidence = max(0.0, min(1.0, 0.45 * data_coverage + 0.35 * sources_agreeing + 0.20))
        spread = max(parts.values()) - min(parts.values())
        reliability = max(0.0, min(1.0, (1 - spread / 100) * 0.7 + 0.3 * sources_agreeing))

        weighted = {k: round(self.weights[k] * parts[k], 3) for k in parts}
        top = sorted(weighted.items(), key=lambda kv: kv[1], reverse=True)
        explanation = {
            "components": {k: round(v, 2) for k, v in parts.items()},
            "weighted_contribution": weighted,
            "weights": self.weights,
            "primary_driver": top[0][0],
            "weakest_driver": top[-1][0],
            "summary": (
                f"{top[0][0].replace('_', ' ')} is the main driver "
                f"({weighted[top[0][0]]:.1f} pts); "
                f"{top[-1][0].replace('_', ' ')} contributes least "
                f"({weighted[top[-1][0]]:.1f} pts)."
            ),
            "inputs": {
                "sentiment": sentiment,
                "attention": attention,
                "velocity": velocity,
                "smart_money": smart_money,
                "volume_growth_pct": volume_growth_pct,
                "price_change_pct": price_change_pct,
            },
        }
        return AlphaResult(
            alpha_score=round(alpha, 2),
            sentiment_score=round(sentiment_component, 2),
            attention_score=round(attention, 2),
            velocity_score=round(velocity, 2),
            smart_money_score=round(smart_money, 2),
            volume_score=round(volume_component, 2),
            confidence=round(confidence, 3),
            reliability=round(reliability, 3),
            classification=classify_alpha(alpha),
            explanation=explanation,
        )

    def diff(self, previous: AlphaResult, current: AlphaResult) -> dict:
        """Explain why the score changed between two runs."""
        deltas = {
            k: round(current.explanation["components"][k] - previous.explanation["components"][k], 2)
            for k in current.explanation["components"]
        }
        driver = max(deltas, key=lambda k: abs(deltas[k]))
        return {
            "delta": round(current.alpha_score - previous.alpha_score, 2),
            "driver": driver,
            "driver_delta": deltas[driver],
            "component_deltas": deltas,
            "summary": (
                f"Alpha moved {current.alpha_score - previous.alpha_score:+.1f} pts; "
                f"{driver.replace('_', ' ')} changed most ({deltas[driver]:+.1f})."
            ),
        }
