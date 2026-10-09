"""Unit tests for TriageGate."""

import pytest
from aegis_common.schemas.enums import MerchantCategory
from aegis_common.schemas.features import CategoryCheck, FeatureVector, MonetaryAnomaly, TravelCheck
from aegis_engine.adapters.mock import MockTelemetrySinkAdapter
from aegis_engine.agents.triage import TriageGate
from aegis_engine.application.telemetry import TelemetryEmitter
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


@pytest.mark.asyncio
async def test_triage_clean_fast_path() -> None:
    gate = TriageGate(name="triage")
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_TRIAGE01", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        monetary=MonetaryAnomaly(z_score=0.2, ratio_to_p95=0.5, is_anomalous=False),
        travel=TravelCheck(speed_kmh=0.0, impossible=False),
        category=CategoryCheck(is_novel=False, is_high_risk=False),
    )

    session = Session(
        app_name="aegis",
        user_id="USR_4401",
        id="sess-triage-clean",
        state={
            "features": features,
            "base_score": 0,
            "merchant_category": MerchantCategory.COFFEE_SHOP,
            "early_contained": False,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-triage-1"
    )

    events = [ev async for ev in gate._run_async_impl(ctx)]
    assert len(events) == 1
    assert events[0].actions.state_delta["triage"] == "FAST_ALLOW"


@pytest.mark.asyncio
async def test_triage_escalates_on_high_score() -> None:
    gate = TriageGate(name="triage")
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_TRIAGE02", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        monetary=MonetaryAnomaly(z_score=5.0, ratio_to_p95=10.0, is_anomalous=True),
        travel=TravelCheck(speed_kmh=1200.0, impossible=True),
        category=CategoryCheck(is_novel=True, is_high_risk=True),
    )

    session = Session(
        app_name="aegis",
        user_id="USR_4402",
        id="sess-triage-escalate",
        state={
            "features": features,
            "base_score": 85,
            "merchant_category": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
            "early_contained": False,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-triage-2"
    )

    events = [ev async for ev in gate._run_async_impl(ctx)]
    assert len(events) == 1
    assert events[0].actions.state_delta["triage"] == "INVESTIGATE"
