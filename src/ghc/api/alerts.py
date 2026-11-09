"""Live alerts and history."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engines.alerts import AlertEngine
from ..models import Alert, Signal, WhaleActivity
from ..schemas import AlertOut

router = APIRouter()
_engine = AlertEngine()


@router.get("", response_model=list[AlertOut])
def list_alerts(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(Alert).order_by(Alert.created_at.desc()).limit(limit)).all()


@router.post("/evaluate/{asset}", response_model=list[AlertOut])
def evaluate(asset: str, db: Session = Depends(get_db)):
    signal = db.scalar(
        select(Signal).where(Signal.asset == asset.upper()).order_by(Signal.timestamp.desc())
    )
    if signal is None:
        return []
    detail = (signal.explanation or {}).get("attention_detail", {})
    sm = (signal.explanation or {}).get("smart_money_detail", {})
    whales = db.scalars(select(WhaleActivity).where(WhaleActivity.asset == asset.upper())).all()
    selling = any(w.action in {"distribution", "exchange_inflow"} for w in whales)
    created: list[Alert] = []
    for decision in _engine.evaluate(
        agi=detail.get("agi", 0.0), smart_money=signal.smart_money_score,
        volume_growth_pct=signal.explanation.get("inputs", {}).get("volume_growth_pct", 0.0),
        sentiment_100=(signal.explanation.get("inputs", {}).get("sentiment", 0.0) + 1) * 50,
        attention=signal.attention_score, velocity=signal.velocity_score,
        oi_change_pct=sm.get("oi_score", 50) - 50, whale_selling=selling,
        funding_extreme=sm.get("funding_score", 50) < 30,
        momentum_slowing=signal.velocity_score < 45,
    ):
        alert = Alert(asset=signal.asset, kind=decision.kind, reason=decision.reason,
                      confidence=decision.confidence, expected_impact=decision.expected_impact,
                      payload=decision.payload)
        db.add(alert)
        created.append(alert)
    db.commit()
    for a in created:
        db.refresh(a)
    return created
