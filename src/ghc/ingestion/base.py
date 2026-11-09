"""Shared HTTP plumbing: timeouts, bounded retries with jitter, structured logs."""
from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import get_settings

log = logging.getLogger("ghc.ingest")


class ConnectorError(RuntimeError):
    pass


@dataclass
class FetchResult:
    source: str
    records: list[dict[str, Any]]
    errors: list[str]


def http_get_json(url: str, *, params: dict | None = None, headers: dict | None = None,
                  timeout: float | None = None, max_retries: int | None = None) -> Any:
    settings = get_settings()
    timeout = timeout or settings.request_timeout_seconds
    retries = max_retries if max_retries is not None else settings.max_retries
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, headers=headers or {}) as client:
                resp = client.get(url, params=params)
                if resp.status_code == 429:
                    raise ConnectorError("rate limited")
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001 - retried below
            last_error = exc
            if attempt < retries - 1:
                sleep = min(8.0, 0.5 * 2**attempt) + random.uniform(0, 0.3)
                log.warning("GET %s failed (%s); retry in %.1fs", url, exc, sleep)
                time.sleep(sleep)
    raise ConnectorError(f"GET {url} failed after {retries} attempts: {last_error}")


class BaseConnector(ABC):
    name: str = "base"

    def __init__(self) -> None:
        self.settings = get_settings()

    @abstractmethod
    def fetch(self, **kwargs) -> FetchResult: ...

    def run(self, **kwargs) -> FetchResult:
        try:
            result = self.fetch(**kwargs)
            log.info("%s: %d records", self.name, len(result.records))
            return result
        except Exception as exc:
            log.exception("%s failed", self.name)
            return FetchResult(source=self.name, records=[], errors=[str(exc)])
