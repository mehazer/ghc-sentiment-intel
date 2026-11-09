from datetime import UTC, datetime, timedelta

from ghc.engines.attention import attention_snapshot


def test_spike_is_flagged_as_anomaly():
    now = datetime(2026, 1, 31, tzinfo=UTC)
    base = [now - timedelta(days=d, hours=2) for d in range(1, 30) for _ in range(2)]
    spike = [now - timedelta(hours=h) for h in range(20)]
    snap = attention_snapshot(base + spike, now)
    assert snap.agi > 2.5
    assert snap.is_anomaly
    assert snap.velocity > 0


def test_quiet_asset_scores_low():
    now = datetime(2026, 1, 31, tzinfo=UTC)
    sparse = [now - timedelta(days=d) for d in range(1, 30)]
    snap = attention_snapshot(sparse, now)
    assert snap.agi < 1.5
    assert snap.score < 60


def test_empty_history_is_safe():
    now = datetime(2026, 1, 31, tzinfo=UTC)
    snap = attention_snapshot([], now)
    assert snap.mentions_current == 0
    assert snap.score == 0
