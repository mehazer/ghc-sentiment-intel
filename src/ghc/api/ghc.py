"""GHC threshold, playbook, trade and risk endpoints."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..ghc import (
    ThresholdConfig,
    build_risk_report,
    classify,
    detect_outliers,
    outlier_ratio,
    playbook_for,
)
from ..models import GHCState, PlaybookEvent, Signal, Trade
from ..schemas import BalanceIn, GHCStateOut, PlaybookOut, TradeIn, TradeOut

router = APIRouter()


def _config() -> ThresholdConfig:
    s = get_settings()
    return ThresholdConfig(s.ghc_s1, s.ghc_s2, s.ghc_b1, s.ghc_b2)


def _state(db: Session) -> GHCState:
    state = db.get(GHCState, 1)
    if state is None:
        state = GHCState(id=1)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.post("/balance", response_model=GHCStateOut)
def set_balance(payload: BalanceIn, db: Session = Depends(get_db)):
    state = _state(db)
    result = classify(payload.current_equity, payload.balance_line, _config())
    state.balance_line = payload.balance_line
    state.deviation_pct = result.deviation_pct
    state.zone = result.zone.value
    state.daily_pnl_forecast = payload.daily_pnl_forecast
    state.csi = payload.csi
    state.cri_olr = payload.cri_olr
    state.cri_brc = payload.cri_brc
    state.updated_at = datetime.now(tz=UTC)
    db.add(PlaybookEvent(zone=result.zone.value, action="balance_update",
                         detail=f"equity {payload.current_equity} vs balance {payload.balance_line}"))
    db.commit()
    db.refresh(state)
    return state


@router.get("/state", response_model=GHCStateOut)
def get_state(db: Session = Depends(get_db)):
    return _state(db)


@router.get("/playbook", response_model=PlaybookOut)
def get_playbook(db: Session = Depends(get_db)):
    from ..ghc.models import Zone

    state = _state(db)
    pb = playbook_for(Zone(state.zone))
    return PlaybookOut(zone=state.zone, deviation_pct=state.deviation_pct,
                       actions=pb.actions, guards=pb.guards, updated_at=state.updated_at)


@router.post("/trades", response_model=TradeOut, status_code=201)
def add_trade(payload: TradeIn, db: Session = Depends(get_db)):
    s = get_settings()
    trade = Trade(**payload.model_dump(), is_outlier=payload.deviation_pct <= s.ghc_outlier_pnl_pct)
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/trades", response_model=list[TradeOut])
def list_trades(status: str | None = None, db: Session = Depends(get_db)):
    q = select(Trade).order_by(Trade.opened_at.desc())
    if status:
        q = q.where(Trade.status == status)
    return db.scalars(q).all()


@router.post("/trades/{trade_id}/close", response_model=TradeOut)
def close_trade(trade_id: int, exit_price: float = Query(...), db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if trade is None:
        raise HTTPException(status_code=404, detail="trade not found")
    direction = 1 if trade.side == "buy" else -1
    trade.pnl_pct = round((exit_price / trade.entry_price - 1) * 100 * direction, 4)
    trade.pnl_usd = round(trade.size_usd * trade.pnl_pct / 100, 2)
    trade.status = "closed"
    trade.closed_at = datetime.now(tz=UTC)
    s = get_settings()
    trade.is_outlier = trade.pnl_pct <= s.ghc_outlier_pnl_pct
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/outliers")
def outliers(db: Session = Depends(get_db)):
    s = get_settings()
    trades = list(db.scalars(select(Trade).where(Trade.status == "open")).all())
    flags = detect_outliers(trades, s.ghc_outlier_pnl_pct)
    return {"ratio": outlier_ratio(trades), "flags": [f.__dict__ for f in flags]}


@router.get("/risk")
def risk(leverage: float = 2.0, funding_rate: float = 0.0, db: Session = Depends(get_db)):
    state = _state(db)
    trades = list(db.scalars(select(Trade).where(Trade.status == "open")).all())
    exposure: dict[str, float] = {}
    for t in trades:
        key = f"{t.basket}"
        exposure[key] = exposure.get(key, 0.0) + t.size_usd
    counts: dict[str, float] = {}
    for t in trades:
        if t.is_outlier:
            counts[t.basket] = counts.get(t.basket, 0.0) + 1 / max(1, len(trades))
    report = build_risk_report(
        deviation_pct=state.deviation_pct, outlier_ratio=outlier_ratio(trades),
        leverage=leverage, funding_rate=funding_rate,
        daily_pnl_forecast_pct=state.daily_pnl_forecast, exposure=exposure, outlier_counts=counts,
    )
    return report.__dict__


@router.get("/candidates")
def candidates(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Rank current signals into buy/sell candidates for the active zone side."""
    from ..ghc import decision_indicator, rank_candidates
    from ..ghc.models import Side

    state = _state(db)
    rows = db.scalars(select(Signal).order_by(Signal.timestamp.desc()).limit(2000)).all()
    latest: dict[str, Signal] = {}
    for row in rows:
        latest.setdefault(row.asset, row)

    side = Side.SELL if state.deviation_pct > 0 else Side.BUY
    pool = [{
        "symbol": asset,
        "alpha_score": sig.alpha_score,
        "smart_money": sig.smart_money_score,
        "sentiment": sig.sentiment_score / 50 - 1,
    } for asset, sig in latest.items()]

    ranked = rank_candidates(pool, side)[:limit]
    di = decision_indicator(ranked, side)
    return {
        "side": side.value,
        "candidates": [c.__dict__ for c in ranked],
        "decision": di.__dict__,
    }
