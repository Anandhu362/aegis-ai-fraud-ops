"""Unit tests for BehavioralAnalystAgent and ThreatIntelAgent."""

import pytest
from aegis_common.schemas.features import (
    DeviceCheck,
    FeatureVector,
    IpReputation,
    MonetaryAnomaly,
    TravelCheck,
    VelocityStats,
)
from aegis_engine.adapters.mock import MockTelemetrySinkAdapter
from aegis_engine.agents.behavioral import BehavioralAnalystAgent
from aegis_engine.agents.threat_intel import ThreatIntelAgent
from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import BehavioralReport, ThreatReport
from aegis_engine.settings import EngineSettings
from google.adk.agents import InvocationContext
from google.adk.sessions import InMemorySessionService, Session


@pytest.mark.asyncio
async def test_behavioral_analyst_fast_path() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = BehavioralAnalystAgent(name="behavioral_analyst", settings=settings)
    session_service = InMemorySessionService()
    session = Session(
        app_name="aegis",
        user_id="USR_4401",
        id="sess-spec-1",
        state={"triage": "FAST_ALLOW"},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-spec-1"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    report: BehavioralReport = events[0].actions.state_delta["behavioral_report"]
    assert report.behavioral_anomaly_score == 0
    assert report.is_structuring_suspected is False


@pytest.mark.asyncio
async def test_threat_intel_fast_path() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = ThreatIntelAgent(name="threat_intel", settings=settings)
    session_service = InMemorySessionService()
    session = Session(
        app_name="aegis",
        user_id="USR_4401",
        id="sess-spec-2",
        state={"triage": "FAST_ALLOW"},
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-spec-2"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    report: ThreatReport = events[0].actions.state_delta["threat_report"]
    assert report.threat_intel_score == 0
    assert report.is_tor is False


@pytest.mark.asyncio
async def test_behavioral_analyst_generates_mock_report_when_escalated() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = BehavioralAnalystAgent(name="behavioral_analyst", settings=settings)
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_SPEC01", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        monetary=MonetaryAnomaly(z_score=6.5, ratio_to_p95=12.0, is_anomalous=True),
        velocity=VelocityStats(structuring_hit=True, near_threshold_count_15m=3),
    )

    session = Session(
        app_name="aegis",
        user_id="USR_4403",
        id="sess-spec-3",
        state={
            "triage": "INVESTIGATE",
            "features": features,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-spec-3"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    report: BehavioralReport = events[0].actions.state_delta["behavioral_report"]
    assert report.is_structuring_suspected is True
    assert report.behavioral_anomaly_score > 50
    assert "velocity.structuring_hit" in report.cited_features


@pytest.mark.asyncio
async def test_threat_intel_generates_mock_report_when_escalated() -> None:
    settings = EngineSettings(aegis_adapter_mode="mock")
    agent = ThreatIntelAgent(name="threat_intel", settings=settings)
    sink = MockTelemetrySinkAdapter()
    emitter = TelemetryEmitter(tx_id="TX_SPEC02", sink=sink)
    session_service = InMemorySessionService()

    features = FeatureVector(
        ip=IpReputation(is_tor=True, abuse_score=95),
        travel=TravelCheck(speed_kmh=15000.0, impossible=True),
        device=DeviceCheck(is_new=True),
    )

    session = Session(
        app_name="aegis",
        user_id="USR_4402",
        id="sess-spec-4",
        state={
            "triage": "INVESTIGATE",
            "features": features,
            "emitter": emitter,
        },
        last_update_time=0.0,
    )
    ctx = InvocationContext(
        session=session, session_service=session_service, invocation_id="inv-spec-4"
    )

    events = [ev async for ev in agent._run_async_impl(ctx)]
    assert len(events) == 1
    report: ThreatReport = events[0].actions.state_delta["threat_report"]
    assert report.threat_intel_score >= 90
    assert report.is_tor is True
    assert report.is_impossible_travel is True
    assert "ip.is_tor" in report.cited_features
