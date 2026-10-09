"""Unit tests for pure geographic calculations and travel velocity."""

from datetime import UTC, datetime, timedelta

from aegis_common.schemas.enums import Channel
from aegis_engine.domain.geo import (
    compute_haversine_distance,
    compute_travel_speed,
    evaluate_travel,
)


def test_haversine_same_point() -> None:
    """Distance between identical coordinates must be exactly zero."""
    dist = compute_haversine_distance(25.2048, 55.2708, 25.2048, 55.2708)
    assert dist == 0.0


def test_haversine_london_to_dubai() -> None:
    """Distance between London and Dubai should be approximately 5,470 km."""
    london_lat, london_lon = 51.5074, -0.1278
    dubai_lat, dubai_lon = 25.2048, 55.2708

    dist = compute_haversine_distance(london_lat, london_lon, dubai_lat, dubai_lon)
    assert 5400.0 < dist < 5550.0


def test_haversine_antimeridian_crossing() -> None:
    """Haversine must correctly compute shortest great-circle across the 180th meridian."""
    dist = compute_haversine_distance(0.0, -179.0, 0.0, 179.0)
    # 2 degrees along equator is ~ 222 km
    assert 220.0 < dist < 225.0


def test_compute_travel_speed_normal() -> None:
    """Speed across 100 km in 1 hour is 100 km/h."""
    speed = compute_travel_speed(100.0, 3600.0)
    assert speed == 100.0


def test_compute_travel_speed_zero_elapsed_clamped() -> None:
    """Zero elapsed seconds should be clamped to 1 minute to avoid division by zero."""
    speed = compute_travel_speed(10.0, 0.0)
    # 10 km in 1 minute = 600 km/h
    assert speed == 600.0


def test_evaluate_travel_impossible_tor_attack() -> None:
    """Dubai POS to London in 12 minutes must trigger impossible travel flag."""
    t0 = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(minutes=12)

    result = evaluate_travel(
        lat1=25.2048,
        lon1=55.2708,
        ts1=t0,
        channel1=Channel.CARD_PRESENT,
        lat2=51.5074,
        lon2=-0.1278,
        ts2=t1,
        channel2=Channel.ECOMMERCE,
        prev_city="Dubai",
    )

    assert result.impossible is True
    assert result.exempt is False
    assert result.speed_kmh > 20000.0
    assert result.distance_km > 5400.0


def test_evaluate_travel_card_present_exemption() -> None:
    """Two CARD_PRESENT transactions within 30 km must be exempt from travel alerts."""
    t0 = datetime(2026, 10, 9, 12, 0, 0, tzinfo=UTC)
    t1 = t0 + timedelta(minutes=1)

    result = evaluate_travel(
        lat1=25.2048,
        lon1=55.2708,
        ts1=t0,
        channel1=Channel.CARD_PRESENT,
        lat2=25.2500,
        lon2=55.3000,
        ts2=t1,
        channel2=Channel.CARD_PRESENT,
    )

    assert result.distance_km < 50.0
    assert result.exempt is True
    assert result.impossible is False
