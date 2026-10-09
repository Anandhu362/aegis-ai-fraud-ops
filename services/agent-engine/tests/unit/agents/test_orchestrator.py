"""Unit tests for OrchestratorAgent."""

import pytest
from aegis_common.schemas.enums import Typology
from aegis_common.schemas.features import (
    DeviceCheck,
    FeatureVector,
    IpReputation,
    MonetaryAnomaly,
    TravelCheck,
    VelocityStats,
)
from aegis_common.schemas.verdict import ScoreBreakdown
from aegis_engine.adapters.mock import MockTelemetrySinkAdapter
from aegis_engine.agents.orchestrator import OrchestratorAgent
from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import BehavioralReport, OrchestratorAssessment, ThreatReport
from aegis_engine.settings import EngineSettings
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


@pytest.mark.asyncio
async def test_orchestrator_fast_path() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = OrchestratorAgent(name="orchestrator", settings=settings)
    session_service = InMemorySessionService()
    session = Session(
        app_name="aegis",
        user_id="USR_4401",
        id="sess-orch-1",
        state={"triage": "FAST_ALLOW"},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-orch-1"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    assessment: OrchestratorAssessment = events[0].actions.state_delta["orchestrator_assessment"]
    assert assessment.typology == Typology.NONE
    assert assessment.score_adjustment == 0


@pytest.mark.asyncio
async def test_orchestrator_synthesizes_ato_assessment() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = OrchestratorAgent(name="orchestrator", settings=settings)
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_ORCH01", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        ip=IpReputation(is_tor=True),
        travel=TravelCheck(speed_kmh=12000.0, impossible=True),
        monetary=MonetaryAnomaly(z_score=7.0, is_anomalous=True),
        device=DeviceCheck(is_new=True),
    )
    b_report = BehavioralReport(
        is_structuring_suspected=False,
        behavioral_anomaly_score=80,
        monetary_risk_level="HIGH",
        findings=["High deviation"],
    )
    t_report = ThreatReport(
        is_tor=True,
        is_vpn=False,
        is_impossible_travel=True,
        threat_intel_score=100,
        network_risk_level="CRITICAL",
        findings=["Tor + impossible travel"],
    )
    score_breakdown = ScoreBreakdown(base=90, floor=90, llm_adjustment=0, signals={}, rules=["H1"])

    session = Session(
        app_name="aegis",
        user_id="USR_4402",
        id="sess-orch-2",
        state={
            "triage": "INVESTIGATE",
            "features": features,
            "behavioral_report": b_report,
            "threat_report": t_report,
            "score_breakdown": score_breakdown,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-orch-2"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    assessment: OrchestratorAssessment = events[0].actions.state_delta["orchestrator_assessment"]
    assert assessment.typology == Typology.ACCOUNT_TAKEOVER
    assert -10 <= assessment.score_adjustment <= 10
    assert "ip.is_tor" in assessment.cited_evidence


@pytest.mark.asyncio
async def test_orchestrator_synthesizes_structuring_assessment() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = OrchestratorAgent(name="orchestrator", settings=settings)
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_ORCH02", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        velocity=VelocityStats(structuring_hit=True, near_threshold_count_15m=3),
        monetary=MonetaryAnomaly(z_score=6.0, is_anomalous=True),
    )
    b_report = BehavioralReport(
        is_structuring_suspected=True,
        behavioral_anomaly_score=85,
        monetary_risk_level="HIGH",
        findings=["Structuring hit"],
    )
    t_report = ThreatReport(
        is_tor=False,
        is_vpn=False,
        is_impossible_travel=False,
        threat_intel_score=0,
        network_risk_level="LOW",
        findings=["Clean"],
    )
    score_breakdown = ScoreBreakdown(base=75, floor=72, llm_adjustment=0, signals={}, rules=["H2"])

    session = Session(
        app_name="aegis",
        user_id="USR_4403",
        id="sess-orch-3",
        state={
            "triage": "INVESTIGATE",
            "features": features,
            "behavioral_report": b_report,
            "threat_report": t_report,
            "score_breakdown": score_breakdown,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-orch-3"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    assessment: OrchestratorAssessment = events[0].actions.state_delta["orchestrator_assessment"]
    assert assessment.typology == Typology.STRUCTURING
    assert -10 <= assessment.score_adjustment <= 10
