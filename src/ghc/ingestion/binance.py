"""Binance spot + futures public data (price, volume, funding, OI)."""
from __future__ import annotations

from datetime import UTC, datetime

from .base import BaseConnector, FetchResult, http_get_json


class BinanceConnector(BaseConnector):
    name = "binance"

    def fetch(self, symbols: list[str] | None = None, interval: str = "1h", limit: int = 48) -> FetchResult:
        symbols = [s.upper().replace("/", "") for s in (symbols or ["BTCUSDT", "ETHUSDT"])]
        base = self.settings.binance_base_url
        records = []
        errors = []
        for symbol in symbols:
            try:
                klines = http_get_json(
                    f"{base}/api/v3/klines",
                    params={"symbol": symbol, "interval": interval, "limit": limit},
                )
                premium = http_get_json(f"{base}/fapi/v1/premiumIndex", params={"symbol": symbol})
                oi = http_get_json(f"{base}/fapi/v1/openInterest", params={"symbol": symbol})
                asset = symbol.removesuffix("USDT")
                for k in klines:
                    records.append({
                        "asset": asset,
                        "price": float(k[4]),
                        "volume": float(k[5]),
                        "open_interest": float(oi.get("openInterest", 0.0)),
                        "funding_rate": float(premium.get("lastFundingRate", 0.0)),
                        "liquidations": None,
                        "timestamp": datetime.fromtimestamp(k[0] / 1000, tz=UTC).isoformat(),
                    })
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{symbol}: {exc}")
        return FetchResult(source=self.name, records=records, errors=errors)
