"""Rule-based alert engine covering accumulation, breakout, FOMO and tops."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AlertDecision:
    kind: str
    reason: str
    confidence: float
    expected_impact: str
    payload: dict = field(default_factory=dict)


class AlertEngine:
    """Each rule returns at most one alert; strongest rules win."""

    def evaluate(self, *, agi: float, smart_money: float, volume_growth_pct: float,
                 sentiment_100: float, attention: float, velocity: float,
                 oi_change_pct: float, whale_selling: bool, funding_extreme: bool,
                 momentum_slowing: bool) -> list[AlertDecision]:
        out: list[AlertDecision] = []

        if agi > 2.5 and smart_money > 60 and volume_growth_pct > 50 and sentiment_100 > 60:
            out.append(AlertDecision(
                kind="early_accumulation",
                reason=(f"AGI {agi:.2f}× baseline, smart money {smart_money:.0f}, "
                        f"volume +{volume_growth_pct:.0f}%, sentiment {sentiment_100:.0f}. "
                        "Attention is building while price is still quiet."),
                confidence=min(0.95, 0.5 + 0.1 * min(4, agi) + 0.02 * (smart_money - 50)),
                expected_impact="high",
                payload={"agi": agi, "smart_money": smart_money, "volume_growth_pct": volume_growth_pct},
            ))

        if velocity > 0 and oi_change_pct > 0 and agi > 1.5:
            out.append(AlertDecision(
                kind="breakout_watch",
                reason=(f"Velocity +{velocity:.0f} with open interest +{oi_change_pct:.0f}% "
                        f"and AGI {agi:.2f}×. New money entering as attention accelerates."),
                confidence=min(0.9, 0.45 + 0.05 * min(6, agi) + 0.01 * oi_change_pct),
                expected_impact="high",
                payload={"velocity": velocity, "oi_change_pct": oi_change_pct, "agi": agi},
            ))

        if sentiment_100 > 90 and attention > 90 and (whale_selling or funding_extreme):
            out.append(AlertDecision(
                kind="fomo_warning",
                reason=(f"Sentiment {sentiment_100:.0f} and attention {attention:.0f} are extreme, "
                        f"while {'whales are selling' if whale_selling else 'funding is stretched'}. "
                        "Late-stage crowding."),
                confidence=0.75 if whale_selling and funding_extreme else 0.62,
                expected_impact="high",
                payload={"sentiment": sentiment_100, "attention": attention},
            ))

        if sentiment_100 > 85 and attention > 85 and whale_selling and momentum_slowing:
            out.append(AlertDecision(
                kind="possible_top",
                reason=("Retail attention is at an extreme, whales are distributing and momentum "
                        "is slowing. Distribution into strength."),
                confidence=0.7,
                expected_impact="high",
                payload={"sentiment": sentiment_100, "attention": attention},
            ))
        return out
