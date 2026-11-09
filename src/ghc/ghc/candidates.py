"""Buy/sell basket candidate flow.

Flow from the sketch: analyse current position → check alignment with strategy →
check targets met → trade. Position is only allowed to shrink risk inside the
neutral band; adding requires alignment and a met target.
"""
from __future__ import annotations

from .models import Candidate, DecisionIndicator, Side


def strategy_alignment(alpha_score: float, zone_side: Side, smart_money: float,
                       sentiment: float) -> float:
    """0-100 agreement between the signal engine and the side we would take."""
    alpha = max(0.0, min(100.0, alpha_score))
    sm = max(0.0, min(100.0, smart_money))
    sent = (max(-1.0, min(1.0, sentiment)) + 1) * 50
    directional = (alpha + sm + sent) / 3
    if zone_side == Side.BUY:
        return round(directional, 2)
    return round(100 - directional, 2)


def targets_met(candidate_price: float, target_price: float, side: Side, tolerance_pct: float = 0.0) -> bool:
    if side == Side.BUY:
        return candidate_price <= target_price * (1 + tolerance_pct / 100)
    return candidate_price >= target_price * (1 - tolerance_pct / 100)


def build_candidate(symbol: str, side: Side, alpha_score: float, smart_money: float,
                    sentiment: float, price: float, target: float,
                    min_alignment: float = 60.0) -> Candidate | None:
    alignment = strategy_alignment(alpha_score, side, smart_money, sentiment)
    met = targets_met(price, target, side)
    reasons = [
        f"alpha {alpha_score:.0f}",
        f"smart money {smart_money:.0f}",
        f"alignment {alignment:.0f}",
        "target met" if met else "target not met",
    ]
    if alignment >= min_alignment and met:
        return Candidate(symbol=symbol, side=side,
                         confidence=round(alignment, 2), reasons=reasons)
    return None


def decision_indicator(candidates: list[Candidate], zone_side: Side) -> DecisionIndicator:
    """GHC Composite Decision Indicator (GHC-CDI), 0-100 confidence."""
    if not candidates:
        return DecisionIndicator(label="No Trade", score=0.0, alignment=0.0, components={})
    side_bias = sum(c.confidence for c in candidates) / len(candidates)
    agreement = sum(1 for c in candidates if c.side is zone_side) / len(candidates) * 100
    strength = max(c.confidence for c in candidates)
    score = 0.45 * side_bias + 0.35 * agreement + 0.20 * strength
    if score >= 85:
        label = "Strong Accumulate" if zone_side == Side.BUY else "Strong Distribute"
    elif score >= 70:
        label = "Accumulate" if zone_side == Side.BUY else "Distribute"
    elif score >= 55:
        label = "Watch"
    else:
        label = "No Trade"
    return DecisionIndicator(
        label=label, score=round(score, 2), alignment=round(agreement, 2),
        components={
            "side_bias": round(side_bias, 2),
            "agreement": round(agreement, 2),
            "strength": round(strength, 2),
        },
    )


def rank_candidates(rows: list[dict], side: Side,
                    min_alignment: float = 0.0) -> list[Candidate]:
    """Rank assets for a side using alignment only.

    Use this when no per-asset target price exists yet; ``build_candidate`` stays
    the gate for execution, where a target must actually be met.
    """
    out: list[Candidate] = []
    for row in rows:
        alignment = strategy_alignment(
            row["alpha_score"], side, row["smart_money"], row["sentiment"],
        )
        if alignment < min_alignment:
            continue
        out.append(Candidate(
            symbol=row["symbol"], side=side, confidence=round(alignment, 2),
            reasons=[
                f"alpha {row['alpha_score']:.0f}",
                f"smart money {row['smart_money']:.0f}",
                f"alignment {alignment:.0f}",
            ],
        ))
    return sorted(out, key=lambda c: c.confidence, reverse=True)
