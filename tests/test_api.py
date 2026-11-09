def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_ingest_and_score_flow(client):
    import datetime as dt

    now = dt.datetime.now(dt.UTC)
    posts = [
        {"post_id": "p1", "timestamp": (now - dt.timedelta(hours=1)).isoformat(), "asset": "BTC",
         "source": "x", "text": "BTC whale accumulation, breakout soon 🚀", "followers": 90000,
         "likes": 900, "comments": 60, "shares": 200, "verified": True},
        {"post_id": "p2", "timestamp": (now - dt.timedelta(hours=2)).isoformat(), "asset": "BTC",
         "source": "reddit", "text": "strong bullish momentum on ETF approval", "followers": 5000},
    ]
    r = client.post("/api/ingest/posts", json=posts)
    assert r.status_code == 201, r.text
    assert len(r.json()) == 2

    metrics = [{"asset": "BTC", "price": 100 + i, "volume": 1000 + i * 50, "open_interest": 5000 + i * 100,
                "funding_rate": 0.0001, "timestamp": (now - dt.timedelta(hours=6 - i)).isoformat()}
               for i in range(6)]
    assert client.post("/api/ingest/market", json=metrics).status_code == 201

    whales = [{"wallet": "w1", "asset": "BTC", "value_usd": 2_000_000, "action": "accumulation",
               "timestamp": (now - dt.timedelta(hours=3)).isoformat()}]
    assert client.post("/api/ingest/whales", json=whales).status_code == 201

    score = client.post("/api/signals/btc/compute")
    assert score.status_code == 200, score.text
    body = score.json()
    assert 0 <= body["alpha_score"] <= 100
    assert body["classification"]
    assert body["explanation"]["primary_driver"]


def test_spam_posts_are_dropped(client):
    import datetime as dt

    now = dt.datetime.now(dt.UTC)
    r = client.post("/api/ingest/posts", json=[{
        "post_id": "spam1", "timestamp": now.isoformat(), "asset": "ETH", "source": "x",
        "text": "FREE CRYPTO GIVEAWAY click here to double your money"}])
    assert r.status_code == 201
    assert r.json() == []


def test_ghc_balance_and_playbook(client):
    r = client.post("/api/ghc/balance", json={"balance_line": 100000, "current_equity": 165000,
                                              "daily_pnl_forecast": 250, "csi": 81})
    assert r.status_code == 200
    assert r.json()["zone"] == "sell_1"
    pb = client.get("/api/ghc/playbook").json()
    assert any("buy limits" in a.lower() for a in pb["actions"])


def test_trades_and_outliers(client):
    r = client.post("/api/ghc/trades", json={"basket": "buy", "symbol": "BTC", "side": "buy",
                                             "size_usd": 1000, "entry_price": 100, "deviation_pct": 0})
    trade_id = r.json()["id"]
    closed = client.post(f"/api/ghc/trades/{trade_id}/close", params={"exit_price": 90})
    assert closed.status_code == 200
    assert closed.json()["pnl_pct"] == -10.0
    assert closed.json()["is_outlier"] is True

    client.post("/api/ghc/trades", json={"basket": "sell", "symbol": "ETH", "side": "sell",
                                         "size_usd": 500, "entry_price": 200, "deviation_pct": -6})
    out = client.get("/api/ghc/outliers").json()
    assert out["ratio"] > 0


def test_risk_endpoint(client):
    client.post("/api/ghc/balance", json={"balance_line": 100000, "current_equity": 220000})
    risk = client.get("/api/ghc/risk", params={"leverage": 6, "funding_rate": 0.001}).json()
    assert risk["level"] in {"normal", "elevated", "critical"}
    assert risk["olr"] > 0
