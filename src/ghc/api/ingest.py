"""Ingestion endpoints. Connectors are rate-limited; this is the write path."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import MarketMetric, News, Post, WhaleActivity
from ..nlp import NLPEngine
from ..schemas import MarketMetricIn, NewsIn, PostIn, PostOut, WhaleIn

router = APIRouter()
_engine = NLPEngine()


@router.post("/posts", response_model=list[PostOut], status_code=201)
def ingest_posts(payload: list[PostIn], db: Session = Depends(get_db)):
    out: list[Post] = []
    for item in payload:
        enriched = _engine.enrich(item)
        if enriched.is_spam:
            continue
        existing = db.scalar(select(Post).where(Post.post_id == item.post_id))
        if existing:
            continue
        post = Post(
            post_id=item.post_id, timestamp=item.timestamp, asset=item.asset.upper(),
            source=item.source, author=item.author, followers=item.followers, text=item.text,
            likes=item.likes, comments=item.comments, shares=item.shares,
            sentiment=enriched.sentiment, sentiment_label=enriched.sentiment_label,
            influence_score=enriched.influence_score, engagement_score=enriched.engagement_score,
            is_bot=enriched.is_bot, narrative=enriched.narrative, language=enriched.language,
        )
        db.add(post)
        out.append(post)
    db.commit()
    for post in out:
        db.refresh(post)
    return out


@router.post("/market", status_code=201)
def ingest_market(payload: list[MarketMetricIn], db: Session = Depends(get_db)):
    for item in payload:
        db.add(MarketMetric(**item.model_dump() | {"asset": item.asset.upper()}))
    db.commit()
    return {"inserted": len(payload)}


@router.post("/whales", status_code=201)
def ingest_whales(payload: list[WhaleIn], db: Session = Depends(get_db)):
    for item in payload:
        db.add(WhaleActivity(**item.model_dump() | {"asset": item.asset.upper()}))
    db.commit()
    return {"inserted": len(payload)}


@router.post("/news", status_code=201)
def ingest_news(payload: list[NewsIn], db: Session = Depends(get_db)):
    for item in payload:
        sentiment, _ = _engine.sentiment(item.headline)
        db.add(News(**item.model_dump() | {"sentiment": sentiment}))
    db.commit()
    return {"inserted": len(payload)}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok"}
