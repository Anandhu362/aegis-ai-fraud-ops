"""Unit tests for ADK enrichment tools using in-memory mock adapters."""

from datetime import UTC, datetime

import pytest
from aegis_common.schemas.enums import Channel
from aegis_engine.adapters.mock.in_memory_profiles import InMemoryProfileStore
from aegis_engine.adapters.mock.static_ip_intel import StaticIpIntelAdapter
from aegis_engine.tools.baseline import get_user_baseline
from aegis_engine.tools.device import check_device
from aegis_engine.tools.ip_reputation import lookup_ip_reputation
from aegis_engine.tools.travel import verify_velocity_travel
from aegis_engine.tools.velocity import get_velocity_window


@pytest.mark.asyncio
async def test_get_user_baseline_known_user() -> None:
    """Known user USR_4401 returns valid baseline with coffee habits."""
    store = InMemoryProfileStore()
    baseline = await get_user_baseline("USR_4401", store)
    assert baseline.cold_start is False
    assert baseline.avg_amount == 6.50
    assert "coffee_shop" in baseline.known_categories


@pytest.mark.asyncio
async def test_get_user_baseline_unknown_user_cold_start() -> None:
    """Unknown user returns cold start baseline."""
    store = InMemoryProfileStore()
    baseline = await get_user_baseline("USR_UNKNOWN", store)
    assert baseline.cold_start is True


@pytest.mark.asyncio
async def test_lookup_ip_reputation_tor_node() -> None:
    """Tor exit node IP is flagged with high abuse score."""
    intel = StaticIpIntelAdapter()
    rep = await lookup_ip_reputation("185.220.101.5", intel)
    assert rep.is_tor is True
    assert rep.abuse_score >= 90


@pytest.mark.asyncio
async def test_lookup_ip_reputation_clean() -> None:
    """Clean IP returns benign reputation."""
    intel = StaticIpIntelAdapter()
    rep = await lookup_ip_reputation("73.189.42.11", intel)
    assert rep.is_tor is False
    assert rep.is_vpn is False


@pytest.mark.asyncio
async def test_verify_velocity_travel_impossible() -> None:
    """Victim USR_4402 has last tx in Dubai 12 min ago; London tx triggers impossible travel."""
    store = InMemoryProfileStore()
    now = datetime.now(UTC)

    # Destination London: 51.5074, -0.1278
    res = await verify_velocity_travel(
        user_id="USR_4402",
        current_lat=51.5074,
        current_lon=-0.1278,
        current_ts=now,
        current_channel=Channel.ECOMMERCE,
        profile_store=store,
    )

    assert res.impossible is True
    assert res.distance_km > 5000.0


@pytest.mark.asyncio
async def test_verify_velocity_travel_first_time_user() -> None:
    """First-time user with no prior location returns empty default TravelCheck."""
    store = InMemoryProfileStore()
    now = datetime.now(UTC)

    res = await verify_velocity_travel(
        user_id="USR_NEW_USER",
        current_lat=40.7128,
        current_lon=-74.0060,
        current_ts=now,
        current_channel=Channel.ECOMMERCE,
        profile_store=store,
    )

    assert res.distance_km == 0.0
    assert res.impossible is False


@pytest.mark.asyncio
async def test_check_device_known_vs_new() -> None:
    """Test device recognition check."""
    store = InMemoryProfileStore()

    known = await check_device("USR_4401", "DEV_COFFEE_01", store)
    assert known.is_new is False

    novel = await check_device("USR_4401", "DEV_UNKNOWN_99", store)
    assert novel.is_new is True


@pytest.mark.asyncio
async def test_get_velocity_window_structuring_hit() -> None:
    """USR_4403 has prior near-threshold transactions; current tx triggers structuring_hit."""
    store = InMemoryProfileStore()
    now = datetime.now(UTC)

    res = await get_velocity_window(
        user_id="USR_4403",
        current_amount=9600.0,
        current_ts=now,
        profile_store=store,
    )

    assert res.in_structuring_band is True
    assert res.structuring_hit is True
