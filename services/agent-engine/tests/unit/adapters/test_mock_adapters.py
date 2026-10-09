"""Unit tests for mock adapters (Actuator, Telemetry, Profiles, IP intel)."""

import pytest
from aegis_common.schemas.enums import Decision, RiskLevel, TelemetryAction
from aegis_common.schemas.telemetry import TelemetryEvent
from aegis_common.schemas.verdict import Verdict
from aegis_engine.adapters.mock.in_memory_profiles import InMemoryProfileStore
from aegis_engine.adapters.mock.mock_actuator import MockActuatorAdapter
from aegis_engine.adapters.mock.mock_telemetry_sink import MockTelemetrySinkAdapter
from aegis_engine.adapters.mock.static_ip_intel import StaticIpIntelAdapter


@pytest.mark.asyncio
async def test_mock_actuator_operations() -> None:
    """Verify actuator records lockout, transaction block, and alerts in memory."""
    actuator = MockActuatorAdapter()

    assert await actuator.execute_account_lockout("USR_4402", "ATO", "TX_1001") is True
    assert "USR_4402" in actuator.locked_accounts

    assert await actuator.block_transaction("TX_1001", "Structuring") is True
    assert "TX_1001" in actuator.blocked_transactions

    assert await actuator.dispatch_alert("USR_4402", "WHATSAPP_REST", "Fraud detected") is True
    assert len(actuator.dispatched_alerts) == 1
    assert actuator.dispatched_alerts[0]["user_id"] == "USR_4402"


@pytest.mark.asyncio
async def test_mock_telemetry_sink_operations() -> None:
    """Verify telemetry sink buffers events in sequence and stores verdict."""
    sink = MockTelemetrySinkAdapter()

    event = TelemetryEvent(
        seq=1,
        agent="Enrichment Agent",
        action=TelemetryAction.TOOL_RESULT,
        message="Travel speed computed: 27,350 km/h",
        timestamp=1791556200000,
    )
    await sink.emit_event("TX_1001", event)
    assert len(sink.events["TX_1001"]) == 1

    verdict = Verdict(
        tx_id="TX_1001",
        user_id="USR_4402",
        threat_score=100,
        risk_level=RiskLevel.CRITICAL,
        decision=Decision.LOCK_ACCOUNT,
        rationale="Impossible travel + Tor",
    )
    await sink.save_verdict(verdict)
    assert sink.verdicts["TX_1001"].threat_score == 100


@pytest.mark.asyncio
async def test_static_ip_intel_variations() -> None:
    """Test VPN IP and None IP branches."""
    intel = StaticIpIntelAdapter()

    none_rep = await intel.lookup_ip(None)
    assert none_rep.unknown is True

    vpn_rep = await intel.lookup_ip("104.28.0.1")
    assert vpn_rep.is_vpn is True
    assert vpn_rep.is_tor is False


@pytest.mark.asyncio
async def test_in_memory_profile_first_time_user() -> None:
    """Unknown user returns None for last transaction location and empty recent transactions."""
    store = InMemoryProfileStore()
    assert await store.get_last_transaction_location("USR_NONEXISTENT") is None
    assert await store.get_recent_transactions("USR_NONEXISTENT") == []
    assert await store.is_known_device("USR_NONEXISTENT", "DEV_X") is False
