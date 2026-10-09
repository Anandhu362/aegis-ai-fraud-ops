"""Unit tests for statistical anomalies, velocity windowing, and structuring."""

from datetime import UTC, datetime, timedelta

from aegis_common.schemas.features import UserBaseline
from aegis_engine.domain.velocity import (
    compute_monetary_anomaly,
    compute_velocity_stats,
    is_in_structuring_band,
)


def test_monetary_anomaly_benign() -> None:
    """Normal spend near baseline mean should have low Z-score and not be anomalous."""
    baseline = UserBaseline(
        avg_amount=50.0,
        std_amount=10.0,
        median_amount=48.0,
        p95_amount=75.0,
    )
    res = compute_monetary_anomaly(55.0, baseline)
    assert 0.0 < res.z_score < 1.0
    assert res.is_anomalous is False


def test_monetary_anomaly_extreme() -> None:
    """Extreme spend relative to baseline must trigger anomaly flag."""
    baseline = UserBaseline(
        avg_amount=50.0,
        std_amount=15.0,
        median_amount=45.0,
        p95_amount=80.0,
    )
    res = compute_monetary_anomaly(12500.0, baseline)
    assert res.z_score == 10.0  # Clamped at max 10.0
    assert res.is_anomalous is True
    assert res.ratio_to_p95 > 100.0


def test_monetary_anomaly_zero_variance_clamp() -> None:
    """Zero standard deviation in baseline must not trigger division by zero."""
    baseline = UserBaseline(
        avg_amount=4.50,
        std_amount=0.0,  # Zero variance
        median_amount=4.50,
        p95_amount=4.50,
    )
    res = compute_monetary_anomaly(4.50, baseline)
    assert res.z_score == 0.0
    assert res.is_anomalous is False


def test_structuring_band_boundaries() -> None:
    """Verify exact boundaries of $8,000-$9,999 structuring window."""
    assert is_in_structuring_band(7999.99) is False
    assert is_in_structuring_band(8000.00) is True
    assert is_in_structuring_band(9500.00) is True
    assert is_in_structuring_band(9999.99) is True
    assert is_in_structuring_band(10000.00) is False


def test_velocity_and_structuring_hit() -> None:
    """Current tx in band + 2 prior transactions in 15m band must trigger structuring_hit."""
    now = datetime(2026, 10, 9, 14, 0, 0, tzinfo=UTC)
    prior = [
        (now - timedelta(minutes=5), 9500.0),
        (now - timedelta(minutes=10), 9800.0),
    ]

    stats = compute_velocity_stats(9600.0, now, prior)
    assert stats.in_structuring_band is True
    assert stats.near_threshold_count_15m == 3
    assert stats.structuring_hit is True


def test_velocity_single_structuring_no_hit() -> None:
    """Current tx in band with only 1 prior in band should not trigger structuring_hit."""
    now = datetime(2026, 10, 9, 14, 0, 0, tzinfo=UTC)
    prior = [
        (now - timedelta(minutes=5), 9500.0),
        (now - timedelta(minutes=6), 50.0),  # Not in band
    ]

    stats = compute_velocity_stats(9600.0, now, prior)
    assert stats.in_structuring_band is True
    assert stats.structuring_hit is False


def test_velocity_burst_detection() -> None:
    """Five transactions within 60 seconds should count correctly."""
    now = datetime(2026, 10, 9, 14, 0, 0, tzinfo=UTC)
    prior = [
        (now - timedelta(seconds=10), 25.0),
        (now - timedelta(seconds=20), 25.0),
        (now - timedelta(seconds=35), 25.0),
        (now - timedelta(seconds=50), 25.0),
    ]

    stats = compute_velocity_stats(25.0, now, prior)
    assert stats.count_60s == 5
