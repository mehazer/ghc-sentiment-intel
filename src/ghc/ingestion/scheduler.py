"""Bounded scheduler: runs connectors sequentially to respect rate limits."""
from __future__ import annotations

import logging
import time

from ..db import SessionLocal, init_db
from .binance import BinanceConnector

log = logging.getLogger("ghc.scheduler")


def _store_market(records: list[dict]) -> int:
    from ..models import MarketMetric

    with SessionLocal() as db:
        for r in records:
            db.add(MarketMetric(**r))
        db.commit()
    return len(records)


def run_once(symbols: list[str] | None = None) -> dict:
    init_db()
    result = BinanceConnector().run(symbols=symbols)
    stored = _store_market(result.records) if result.records else 0
    return {"stored": stored, "errors": result.errors}


def main(interval: int | None = None) -> None:  # pragma: no cover - long running
    from ..config import get_settings

    interval = interval or get_settings().ingestion_interval_seconds
    init_db()
    while True:
        summary = run_once()
        log.info("cycle complete: %s", summary)
        time.sleep(interval)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()
