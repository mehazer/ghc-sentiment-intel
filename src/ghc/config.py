"""Runtime configuration (12-factor, env driven)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="GHC_", extra="ignore")

    app_name: str = "GHC Sentiment Intelligence"
    env: Literal["dev", "staging", "prod"] = "dev"
    database_url: str = "sqlite:///./ghc.db"
    redis_url: str | None = None
    api_prefix: str = "/api"

    # Ingestion
    ingestion_interval_seconds: int = 60
    x_bearer_token: str | None = None
    reddit_client_id: str | None = None
    reddit_client_secret: str | None = None
    cryptopanic_token: str | None = None
    glassnode_api_key: str | None = None
    whale_alert_api_key: str | None = None
    binance_base_url: str = "https://api.binance.com"
    request_timeout_seconds: float = 10.0
    max_retries: int = 3

    # Scoring weights (must sum to 1.0)
    w_sentiment: float = Field(0.30, ge=0, le=1)
    w_attention: float = Field(0.25, ge=0, le=1)
    w_velocity: float = Field(0.15, ge=0, le=1)
    w_smart_money: float = Field(0.20, ge=0, le=1)
    w_volume: float = Field(0.10, ge=0, le=1)

    # GHC thresholds, expressed as % deviation from the balance line
    ghc_s1: float = 50.0
    ghc_s2: float = 100.0
    ghc_b1: float = -50.0
    ghc_b2: float = -90.0
    ghc_outlier_pnl_pct: float = -3.0

    cors_origins: str = "*"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
