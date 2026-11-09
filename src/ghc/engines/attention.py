"""Attention Growth Index, velocity, acceleration and anomaly detection."""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class AttentionSnapshot:
    mentions_current: int
    mentions_baseline: float
    agi: float
    velocity: float
    acceleration: float
    zscore: float
    is_anomaly: bool
    score: float


def _window_counts(timestamps: list[datetime], now: datetime, window: timedelta) -> int:
    return sum(1 for ts in timestamps if now - window <= ts <= now)


def attention_snapshot(timestamps: list[datetime], now: datetime | None = None,
                       baseline_days: int = 30, recent_hours: int = 24) -> AttentionSnapshot:
    now = now or datetime.now(tz=timestamps[0].tzinfo if timestamps else None)
    recent = _window_counts(timestamps, now, timedelta(hours=recent_hours))
    previous = _window_counts(timestamps, now - timedelta(hours=recent_hours), timedelta(hours=recent_hours))
    day_buckets = []
    for d in range(baseline_days):
        start = now - timedelta(days=d + 1)
        day_buckets.append(_window_counts(timestamps, start, timedelta(days=1)))
    baseline_mean = statistics.fmean(day_buckets) if day_buckets else 0.0
    baseline_sd = statistics.pstdev(day_buckets) if len(day_buckets) > 1 else 0.0

    agi = (recent / baseline_mean) if baseline_mean > 0 else (float(recent) if recent else 0.0)
    velocity = float(recent - previous)
    acceleration = float((recent - previous) - previous)
    z = ((recent - baseline_mean) / baseline_sd) if baseline_sd > 0 else 0.0
    is_anomaly = z >= 2.0 or agi >= 2.5
    # 0-100: AGI 1x = 40, 2.5x = 70, 5x+ = 100
    score = max(0.0, min(100.0, 40.0 * agi if agi <= 1 else 40 + 20 * min(3.0, (agi - 1))))
    if velocity > 0:
        score = min(100.0, score + min(10.0, velocity))
    if acceleration > 0:
        score = min(100.0, score + min(5.0, acceleration / 2))
    return AttentionSnapshot(
        mentions_current=recent,
        mentions_baseline=round(baseline_mean, 2),
        agi=round(agi, 3),
        velocity=velocity,
        acceleration=acceleration,
        zscore=round(z, 3),
        is_anomaly=is_anomaly,
        score=round(score, 2),
    )


class AttentionEngine:
    def __init__(self, baseline_days: int = 30, recent_hours: int = 24) -> None:
        self.baseline_days = baseline_days
        self.recent_hours = recent_hours

    def compute(self, timestamps: list[datetime], now: datetime | None = None) -> AttentionSnapshot:
        return attention_snapshot(timestamps, now, self.baseline_days, self.recent_hours)
