"""Integration tests for InvestigationService end-to-end multi-agent pipeline."""

from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address

import pytest
from aegis_common.schemas.enums import Channel, Decision, MerchantCategory, RiskLevel, Typology
from aegis_common.schemas.transaction import Location, Transaction
from aegis_engine.adapters.mock import (
    InMemoryProfileStore,
    MockActuatorAdapter,
    MockTelemetrySinkAdapter,
    StaticIpIntelAdapter,
)
from aegis_engine.application.run_investigation import InvestigationService


@pytest.fixture
def test_context() -> tuple[
    InvestigationService,
    InMemoryProfileStore,
    StaticIpIntelAdapter,
    MockActuatorAdapter,
    MockTelemetrySinkAdapter,
]:
    profile_store = InMemoryProfileStore()
    ip_intel = StaticIpIntelAdapter()
    actuator = MockActuatorAdapter()
    sink = MockTelemetrySinkAdapter()
    service = InvestigationService(
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
        telemetry_sink=sink,
    )
    return service, profile_store, ip_intel, actuator, sink


@pytest.mark.asyncio
async def test_persona1_clean_coffee_fast_path(
    test_context: tuple[
        InvestigationService,
        InMemoryProfileStore,
        StaticIpIntelAdapter,
        MockActuatorAdapter,
        MockTelemetrySinkAdapter,
    ],
) -> None:
    service, _, _, actuator, sink = test_context
    tx = Transaction(
        tx_id="TX_CLEAN001",
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

    verdict = await service.investigate(tx)

    assert verdict.tx_id == tx.tx_id
    assert verdict.decision == Decision.ALLOW
    assert verdict.threat_score == 0
    assert verdict.risk_level == RiskLevel.LOW
    assert verdict.typology == Typology.NONE
    assert verdict.degraded is False
    assert verdict.event_count >= 4
    assert len(actuator.locked_accounts) == 0
    assert len(actuator.blocked_transactions) == 0
    assert tx.tx_id in sink.verdicts


@pytest.mark.asyncio
async def test_persona2_structuring_burst(
    test_context: tuple[
        InvestigationService,
        InMemoryProfileStore,
        StaticIpIntelAdapter,
        MockActuatorAdapter,
        MockTelemetrySinkAdapter,
    ],
) -> None:
    service, _, _, actuator, _ = test_context
    tx = Transaction(
        tx_id="TX_SMURF001",
        user_id="USR_4403",
        amount=Decimal("9500.00"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant="QuickRemit Global",
        merchant_category=MerchantCategory.MONEY_TRANSFER,
        channel=Channel.ECOMMERCE,
        location=Location(latitude=40.7128, longitude=-74.0060, city="New York", country="US"),
        ip_address=IPv4Address("198.51.100.1"),
        device_id="DEV_SMURF_01",
    )

    verdict = await service.investigate(tx)

    assert verdict.tx_id == tx.tx_id
    assert verdict.decision in [Decision.BLOCK_TX, Decision.LOCK_ACCOUNT]
    assert verdict.threat_score >= 72
    assert verdict.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert verdict.typology == Typology.STRUCTURING
    assert verdict.score_breakdown is not None
    assert "H2" in verdict.score_breakdown.rules
    assert verdict.degraded is False
    assert tx.tx_id in actuator.blocked_transactions


@pytest.mark.asyncio
async def test_persona3_tor_impossible_travel_ato(
    test_context: tuple[
        InvestigationService,
        InMemoryProfileStore,
        StaticIpIntelAdapter,
        MockActuatorAdapter,
        MockTelemetrySinkAdapter,
    ],
) -> None:
    service, _, _, actuator, _ = test_context
    tx = Transaction(
        tx_id="TX_ATO0001",
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

    verdict = await service.investigate(tx)

    assert verdict.tx_id == tx.tx_id
    assert verdict.decision == Decision.LOCK_ACCOUNT
    assert verdict.threat_score >= 90
    assert verdict.risk_level == RiskLevel.CRITICAL
    assert verdict.typology == Typology.ACCOUNT_TAKEOVER
    assert verdict.score_breakdown is not None
    assert "H1" in verdict.score_breakdown.rules
    assert verdict.actuator_action is not None
    assert verdict.actuator_action.account_locked is True
    assert verdict.actuator_action.early_containment is True
    assert "USR_4402" in actuator.locked_accounts
