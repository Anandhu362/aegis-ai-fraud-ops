"""Unit tests for PolicyAgent."""

from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address

import pytest
from aegis_common.schemas.enums import Channel, Decision, MerchantCategory, RiskLevel, Typology
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.transaction import Location, Transaction
from aegis_common.schemas.verdict import ScoreBreakdown
from aegis_engine.adapters.mock import MockActuatorAdapter, MockTelemetrySinkAdapter
from aegis_engine.agents.policy_agent import PolicyAgent
from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import OrchestratorAssessment
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


def _sample_tx(user_id: str = "USR_4401") -> Transaction:
    return Transaction(
        tx_id="TX_POLICY01",
        user_id=user_id,
        amount=Decimal("500.00"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant="Electronics Hub",
        merchant_category=MerchantCategory.ELECTRONICS,
        channel=Channel.ECOMMERCE,
        location=Location(latitude=40.7128, longitude=-74.0060, city="New York", country="US"),
        ip_address=IPv4Address("198.51.100.1"),
        device_id="DEV_POL_01",
    )


@pytest.mark.asyncio
async def test_policy_agent_enforces_h1_hard_floor_regardless_of_negative_adjustment() -> None:
    actuator = MockActuatorAdapter()
    agent = PolicyAgent(name="policy_agent", actuator=actuator)
    sink = MockTelemetrySinkAdapter()
    tx = _sample_tx("USR_4402")
    emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=sink)
    session_service = InMemorySessionService()

    score_breakdown = ScoreBreakdown(
        base=92,
        floor=90,
        llm_adjustment=-10,  # Negative adjustment trying to bring score to 82
        signals={},
        rules=["H1"],
    )

    assessment = OrchestratorAssessment(
        typology=Typology.ACCOUNT_TAKEOVER,
        score_adjustment=-10,
        rationale="Attempting reduction",
    )

    session = Session(
        app_name="aegis",
        user_id=tx.user_id,
        id="sess-pol-1",
        state={
            "tx": tx,
            "features": FeatureVector(),
            "base_score": 92,
            "score_breakdown": score_breakdown,
            "orchestrator_assessment": assessment,
            "triggered_rules": ["H1"],
            "early_contained": False,
            "triage": "INVESTIGATE",
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-pol-1"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    delta = events[0].actions.state_delta
    # Floor is 90, so score cannot drop below 90
    assert delta["final_score"] >= 90
    assert delta["risk_level"] == RiskLevel.CRITICAL
    assert delta["decision"] == Decision.LOCK_ACCOUNT
    assert "USR_4402" in actuator.locked_accounts
    assert tx.tx_id in actuator.blocked_transactions


@pytest.mark.asyncio
async def test_policy_agent_fast_path_allows() -> None:
    actuator = MockActuatorAdapter()
    agent = PolicyAgent(name="policy_agent", actuator=actuator)
    sink = MockTelemetrySinkAdapter()
    tx = _sample_tx("USR_4401")
    emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=sink)
    session_service = InMemorySessionService()

    score_breakdown = ScoreBreakdown(base=0, floor=0, llm_adjustment=0, signals={}, rules=[])

    session = Session(
        app_name="aegis",
        user_id=tx.user_id,
        id="sess-pol-2",
        state={
            "tx": tx,
            "features": FeatureVector(),
            "base_score": 0,
            "score_breakdown": score_breakdown,
            "orchestrator_assessment": None,
            "triggered_rules": [],
            "early_contained": False,
            "triage": "FAST_ALLOW",
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-pol-2"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    delta = events[0].actions.state_delta
    assert delta["final_score"] == 0
    assert delta["risk_level"] == RiskLevel.LOW
    assert delta["decision"] == Decision.ALLOW
    assert len(actuator.locked_accounts) == 0
    assert len(actuator.blocked_transactions) == 0
