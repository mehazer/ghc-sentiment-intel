"""Seed a realistic demo dataset: posts, market history, whales and signals.

Usage: python scripts/seed_demo.py [--db sqlite:///./ghc.db]
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

ASSETS = {"BTC": 67000, "ETH": 3400, "SOL": 165, "ARB": 1.1, "LINK": 16.5}
POSTS = {
    "BTC": ["whale accumulation spotted, spot ETF inflows continue 🚀",
            "breakout above resistance, funding still neutral",
            "institutional adoption keeps building"],
    "ETH": ["layer 2 activity exploding, restaking narrative strong",
            "ETH staking inflows accelerating, bullish structure",
            "upgrade catalyst approaching, accumulation zone"],
    "SOL": ["SOL ecosystem momentum, meme coin volume surging",
            "breakout watch: open interest rising fast",
            "developer activity at all-time high, adoption"],
    "ARB": ["token unlock next week, supply pressure incoming",
            "L2 competition intensifying, outflows from bridge",
            "governance proposal passed, upgrade scheduled"],
    "LINK": ["oracle adoption with major bank integration",
            "whale wallets accumulating LINK steadily",
            "RWA narrative rotating into LINK"],
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("GHC_DATABASE_URL", "sqlite:///./ghc.db"))
    parser.add_argument("--hours", type=int, default=240)
    args = parser.parse_args()
    os.environ["GHC_DATABASE_URL"] = args.db

    from sqlalchemy import delete

    from ghc.db import SessionLocal, init_db
    from ghc.models import MarketMetric, Post, WhaleActivity
    from ghc.nlp import NLPEngine
    from ghc.services.scoring import compute_signal

    random.seed(7)
    init_db()
    engine = NLPEngine()
    now = datetime.now(tz=timezone.utc)

    with SessionLocal() as db:
        db.execute(delete(Post)); db.execute(delete(MarketMetric)); db.execute(delete(WhaleActivity))
        db.commit()

        for asset, base in ASSETS.items():
            for h in range(args.hours, 0, -1):
                drift = math.sin(h / 24) * 0.01 + random.uniform(-0.004, 0.006)
                price = base * (1 + drift * (args.hours - h) / args.hours)
                db.add(MarketMetric(
                    asset=asset, price=round(price, 6),
                    volume=random.uniform(8e5, 2.4e6),
                    open_interest=random.uniform(4e6, 9e6) * (1 + (args.hours - h) / args.hours * 0.15),
                    funding_rate=random.uniform(0.00004, 0.00035),
                    timestamp=now - timedelta(hours=h),
                ))
            for i, text in enumerate(POSTS[asset] * 6):
                db.add(Post(
                    post_id=f"{asset}-{i}", timestamp=now - timedelta(hours=random.randint(1, 36)),
                    asset=asset, source=random.choice(["x", "reddit", "telegram"]),
                    author=f"user{i}", followers=random.choice([1500, 8000, 45000, 220000]),
                    text=text, likes=random.randint(20, 900), comments=random.randint(2, 80),
                    shares=random.randint(5, 200), sentiment=0.0,
                ))
            db.commit()

        posts = db.query(Post).all()
        for p in posts:
            enriched = engine.enrich(p)
            p.sentiment = enriched.sentiment
            p.sentiment_label = enriched.sentiment_label
            p.influence_score = enriched.influence_score
            p.engagement_score = enriched.engagement_score
            p.narrative = enriched.narrative
            p.language = enriched.language
            p.is_bot = enriched.is_bot
        db.commit()

        for asset, base in ASSETS.items():
            for w in range(6):
                action = random.choice(["accumulation", "accumulation", "exchange_outflow", "distribution"])
                db.add(WhaleActivity(
                    wallet=f"0x{random.getrandbits(40):010x}", asset=asset,
                    value_usd=random.uniform(3e5, 4e6), action=action,
                    timestamp=now - timedelta(hours=random.randint(1, 48)),
                ))
        db.commit()

        for asset in ASSETS:
            sig = compute_signal(db, asset)
            print(f"{asset}: alpha={sig.alpha_score:.1f} {sig.classification}")

    print("Demo data seeded.")


if __name__ == "__main__":
    main()
