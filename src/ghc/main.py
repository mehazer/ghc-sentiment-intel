"""FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import api_router
from .config import get_settings
from .db import init_db
from .observability import instrument

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Attention, sentiment and smart-money intelligence for GHC.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)
instrument(app)


@app.get("/health", tags=["ops"])
def health():
    return {"status": "ok", "env": settings.env}


@app.get("/", include_in_schema=False)
def root():
    return JSONResponse({"service": settings.app_name, "docs": "/docs", "api": settings.api_prefix})
