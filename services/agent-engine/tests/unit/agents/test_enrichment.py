"""Unit tests for EnrichmentAgent."""

from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address

import pytest
from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.transaction import Location, Transaction
from aegis_engine.adapters.mock import (
    InMemoryProfileStore,
    MockActuatorAdapter,
    MockTelemetrySinkAdapter,
    StaticIpIntelAdapter,
)
from aegis_engine.agents.enrichment import EnrichmentAgent
from aegis_engine.application.telemetry import TelemetryEmitter
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


@pytest.mark.asyncio
async def test_enrichment_computes_features_and_base_score() -> None:
    profile_store = InMemoryProfileStore()
    ip_intel = StaticIpIntelAdapter()
    actuator = MockActuatorAdapter()
    sink = MockTelemetrySinkAdapter()
    session_service = InMemorySessionService()

    agent = EnrichmentAgent(
        name="enrichment",
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
    )

    tx = Transaction(
        tx_id="TX_ENRICH01",
        user_id="USR_4401",
        amount=Decimal("4.50"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant="Blue Bottle Coffee",
        merchant_category=MerchantCategory.COFFEE_SHOP,
        channel=Channel.CARD_PRESENT,
        location=Location(
            latitude=37.7749, longitude=-122.4194, city="San Francisco", country="US"
        ),
        ip_address=IPv4Address("198.51.100.1"),
        device_id="DEV_COFFEE_01",
    )

    emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=sink)
    session = Session(
        app_name="aegis",
        user_id=tx.user_id,
        id="sess-enrich",
        state={"tx": tx, "emitter": emitter},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-enrich"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    delta = events[0].actions.state_delta
    assert "features" in delta
    assert isinstance(delta["features"], FeatureVector)
    assert "base_score" in delta
    assert delta["base_score"] == 0
    assert delta["early_contained"] is False


@pytest.mark.asyncio
async def test_enrichment_early_containment_on_h1() -> None:
    profile_store = InMemoryProfileStore()
    ip_intel = StaticIpIntelAdapter()
    actuator = MockActuatorAdapter()
    sink = MockTelemetrySinkAdapter()
    session_service = InMemorySessionService()

    agent = EnrichmentAgent(
        name="enrichment",
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
    )

    # USR_4402 has recent tx in Dubai 12 min ago; connecting from London via Tor exit IP
    tx = Transaction(
        tx_id="TX_H1ATO01",
        user_id="USR_4402",
        amount=Decimal("12500.00"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant="Binance Crypto Exchange",
        merchant_category=MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
        channel=Channel.ECOMMERCE,
        location=Location(latitude=51.5074, longitude=-0.1278, city="London", country="GB"),
        ip_address=IPv4Address("185.220.101.5"),  # Tor exit node
        device_id="DEV_UNKNOWN_99",
    )

    emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=sink)
    session = Session(
        app_name="aegis",
        user_id=tx.user_id,
        id="sess-h1",
        state={"tx": tx, "emitter": emitter},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-h1"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    delta = events[0].actions.state_delta
    assert delta["early_contained"] is True
    assert "H1" in delta["triggered_rules"]
    assert "USR_4402" in actuator.locked_accounts
