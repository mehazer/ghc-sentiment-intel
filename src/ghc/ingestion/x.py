"""X/Twitter recent-search connector (requires a bearer token)."""
from __future__ import annotations

from datetime import UTC, datetime

from .base import BaseConnector, FetchResult, http_get_json


class XConnector(BaseConnector):
    name = "x"

    def fetch(self, query: str = "($BTC OR #BTC) -is:retweet lang:en", limit: int = 50) -> FetchResult:
        token = self.settings.x_bearer_token
        if not token:
            return FetchResult(source=self.name, records=[], errors=["GHC_X_BEARER_TOKEN not set"])
        data = http_get_json(
            "https://api.twitter.com/2/tweets/search/recent",
            params={
                "query": query,
                "max_results": max(10, min(100, limit)),
                "tweet.fields": "created_at,public_metrics,lang,author_id",
                "expansions": "author_id",
                "user.fields": "public_metrics,verified,created_at",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        users = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
        records = []
        for tweet in data.get("data", []):
            author = users.get(tweet.get("author_id"), {})
            metrics = tweet.get("public_metrics", {})
            umetrics = author.get("public_metrics", {})
            records.append({
                "post_id": tweet["id"],
                "timestamp": tweet.get("created_at", datetime.now(UTC).isoformat()),
                "asset": "BTC",
                "source": "x",
                "author": author.get("username"),
                "followers": umetrics.get("followers_count", 0),
                "text": tweet["text"],
                "likes": metrics.get("like_count", 0),
                "comments": metrics.get("reply_count", 0),
                "shares": metrics.get("retweet_count", 0),
                "verified": author.get("verified", False),
            })
        return FetchResult(source=self.name, records=records, errors=[])
