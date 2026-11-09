from fastapi import APIRouter

from . import alerts, ghc, ingest, signals

api_router = APIRouter()
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(ghc.router, prefix="/ghc", tags=["ghc"])
