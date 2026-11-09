"""Signal computation and retrieval."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engines.alpha import AlphaEngine
from ..models import Signal
from ..schemas import ScoreOut
from ..services.scoring import compute_signal

router = APIRouter()


def _to_out(sig: Signal) -> ScoreOut:
    return ScoreOut(
        asset=sig.asset, alpha_score=sig.alpha_score, sentiment_score=sig.sentiment_score,
        attention_score=sig.attention_score, velocity_score=sig.velocity_score,
        smart_money_score=sig.smart_money_score, volume_score=sig.volume_score,
        confidence=sig.confidence, reliability=sig.reliability,
        classification=sig.classification, explanation=sig.explanation or {},
        timestamp=sig.timestamp,
    )


@router.post("/{asset}/compute", response_model=ScoreOut)
def compute(asset: str, db: Session = Depends(get_db)):
    return _to_out(compute_signal(db, asset))


@router.get("/ranking", response_model=list[ScoreOut])
def ranking(limit: int = Query(20, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.scalars(select(Signal).order_by(Signal.timestamp.desc()).limit(2000)).all()
    latest: dict[str, Signal] = {}
    for row in rows:
        latest.setdefault(row.asset, row)
    ordered = sorted(latest.values(), key=lambda s: s.alpha_score, reverse=True)[:limit]
    return [_to_out(s) for s in ordered]


@router.get("/{asset}/history", response_model=list[ScoreOut])
def history(asset: str, limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Signal).where(Signal.asset == asset.upper()).order_by(Signal.timestamp.desc()).limit(limit)
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="no signals for asset")
    return [_to_out(s) for s in reversed(rows)]


@router.get("/{asset}/why", response_model=dict)
def why(asset: str, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Signal).where(Signal.asset == asset.upper()).order_by(Signal.timestamp.desc()).limit(2)
    ).all()
    if not rows:
        raise HTTPException(status_code=404, detail="no signals for asset")
    current = rows[0]
    engine = AlphaEngine()
    if len(rows) < 2:
        return {"summary": "First observation for this asset; no comparison available.",
                "explanation": current.explanation}
    prev = rows[1]
    from ..engines.alpha import AlphaResult

    def wrap(s: Signal) -> AlphaResult:
        return AlphaResult(
            alpha_score=s.alpha_score, sentiment_score=s.sentiment_score,
            attention_score=s.attention_score, velocity_score=s.velocity_score,
            smart_money_score=s.smart_money_score, volume_score=s.volume_score,
            confidence=s.confidence, reliability=s.reliability,
            classification=s.classification, explanation=s.explanation or {},
        )
    return engine.diff(wrap(prev), wrap(current))
