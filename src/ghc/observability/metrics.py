"""Prometheus metrics: request count, latency and in-flight requests."""
from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, Histogram, generate_latest

METRICS_PATH = "/metrics"


def _counter(name: str, doc: str, labels: tuple[str, ...]):
    """Reuse an existing collector so app reloads and tests don't collide."""
    existing = REGISTRY._names_to_collectors.get(name)
    return existing or Counter(name, doc, labels)


def _collector(*names: str):
    for name in names:
        found = REGISTRY._names_to_collectors.get(name)
        if found is not None:
            return found
    return None


REQUESTS = _collector("ghc_http_requests_total") or Counter(
    "ghc_http_requests_total", "HTTP requests", ("method", "path", "status")
)
LATENCY = _collector("ghc_http_request_duration_seconds", "ghc_http_request_duration_seconds_bucket",
                     "ghc_http_request_duration_seconds_sum") or Histogram(
    "ghc_http_request_duration_seconds", "Request latency", ("path",)
)
IN_FLIGHT = _collector("ghc_http_in_flight") or Gauge("ghc_http_in_flight", "Requests currently being served")


def instrument(app: FastAPI) -> None:
    @app.middleware("http")
    async def _metrics(request: Request, call_next):
        if request.url.path == METRICS_PATH:
            return await call_next(request)
        IN_FLIGHT.inc()
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            IN_FLIGHT.dec()
        elapsed = time.perf_counter() - started
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        LATENCY.labels(path=path).observe(elapsed)
        REQUESTS.labels(method=request.method, path=path, status=response.status_code).inc()
        return response

    @app.get(METRICS_PATH, include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
