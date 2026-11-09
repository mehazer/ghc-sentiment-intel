"""Crypto news via RSS (CoinDesk, CoinTelegraph, Decrypt)."""
from __future__ import annotations

import re
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx
from defusedxml import ElementTree

from .base import BaseConnector, FetchResult

FEEDS = {
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt": "https://decrypt.co/feed",
}
TAG_RE = re.compile(r"<[^>]+>")


class RSSConnector(BaseConnector):
    name = "rss"

    def fetch(self, feeds: dict[str, str] | None = None, limit: int = 20) -> FetchResult:
        feeds = feeds or FEEDS
        records, errors = [], []
        for source, url in feeds.items():
            try:
                with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                    resp = client.get(url, follow_redirects=True)
                    resp.raise_for_status()
                root = ElementTree.fromstring(resp.content)  # hardened against entity attacks
                for item in root.iter("item"):
                    title = (item.findtext("title") or "").strip()
                    if not title:
                        continue
                    published = item.findtext("pubDate")
                    try:
                        ts = (
                            parsedate_to_datetime(published).astimezone(UTC)
                            if published
                            else datetime.now(UTC)
                        )
                    except (TypeError, ValueError):
                        ts = datetime.now(UTC)
                    records.append({
                        "headline": TAG_RE.sub("", title),
                        "source": source,
                        "url": item.findtext("link"),
                        "timestamp": ts.isoformat(),
                    })
                    if len(records) >= limit:
                        break
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source}: {exc}")
        return FetchResult(source=self.name, records=records, errors=errors)
