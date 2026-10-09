"""Unit tests for IntakeAgent."""

from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address

import pytest
from aegis_common.schemas.enums import Channel, MerchantCategory, TelemetryAction
from aegis_common.schemas.transaction import Location, Transaction
from aegis_engine.adapters.mock import MockTelemetrySinkAdapter
from aegis_engine.agents.intake import IntakeAgent
from aegis_engine.application.telemetry import TelemetryEmitter
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


def _sample_tx(merchant: str = "Test Merchant") -> Transaction:
    return Transaction(
        tx_id="TX_TEST0001",
        user_id="USR_4401",
        amount=Decimal("49.99"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant=merchant,
        merchant_category=MerchantCategory.RETAIL,
        channel=Channel.ECOMMERCE,
        location=Location(
            latitude=37.7749, longitude=-122.4194, city="San Francisco", country="US"
        ),
        ip_address=IPv4Address("198.51.100.1"),
        device_id="DEV_SAFE_01",
    )


@pytest.mark.asyncio
async def test_intake_sanitizes_untrusted_merchant() -> None:
    agent = IntakeAgent(name="intake")
    tx = _sample_tx(merchant="Super Store\x00\x1f\x7f\x9f Inc")
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=sink)
    session_service = InMemorySessionService()

    session = Session(
        app_name="aegis",
        user_id=tx.user_id,
        id="sess-01",
        state={"tx": tx, "emitter": emitter},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-01"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    sanitized_tx: Transaction = events[0].actions.state_delta["tx"]
    assert sanitized_tx.merchant == "Super Store Inc"
    assert "\x00" not in sanitized_tx.merchant
    assert len(emitter.events) == 1
    assert emitter.events[0].action == TelemetryAction.THOUGHT


@pytest.mark.asyncio
async def test_intake_missing_tx_raises_value_error() -> None:
    agent = IntakeAgent(name="intake")
    session_service = InMemorySessionService()
    session = Session(
        app_name="aegis",
        user_id="USR_4401",
        id="sess-02",
        state={},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-02"
    )

    with pytest.raises(ValueError, match="Missing or invalid 'tx'"):
        async for _ in agent._run_async_impl(ctx):
            pass
