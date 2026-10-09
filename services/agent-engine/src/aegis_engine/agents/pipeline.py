"""InvestigationPipeline: Root ADK SequentialAgent coordinating all fraud reasoning agents."""

from google.adk.agents import ParallelAgent, SequentialAgent

from aegis_engine.agents.behavioral import BehavioralAnalystAgent
from aegis_engine.agents.closeout import CloseoutAgent
from aegis_engine.agents.enrichment import EnrichmentAgent
from aegis_engine.agents.intake import IntakeAgent
from aegis_engine.agents.orchestrator import OrchestratorAgent
from aegis_engine.agents.policy_agent import PolicyAgent
from aegis_engine.agents.threat_intel import ThreatIntelAgent
from aegis_engine.agents.triage import TriageGate
from aegis_engine.ports.actuator import ActuatorPort
from aegis_engine.ports.ip_intel import IpIntelPort
from aegis_engine.ports.profile_store import ProfileStore
from aegis_engine.ports.telemetry_sink import TelemetrySinkPort
from aegis_engine.settings import EngineSettings


def build_investigation_pipeline(
    profile_store: ProfileStore | None = None,
    ip_intel: IpIntelPort | None = None,
    actuator: ActuatorPort | None = None,
    telemetry_sink: TelemetrySinkPort | None = None,
    settings: EngineSettings | None = None,
) -> SequentialAgent:
    """Assemble the 8-stage Google ADK multi-agent investigation pipeline.

    Topology:
      SequentialAgent:
        1. IntakeAgent (Deterministic validation and sanitization)
        2. EnrichmentAgent (Deterministic parallel tools & early containment)
        3. TriageGate (Deterministic circuit breaker fast-path)
        4. ParallelAgent:
             - BehavioralAnalystAgent (Gemini Flash-Lite / Mock)
             - ThreatIntelAgent (Gemini Flash-Lite / Mock)
        5. OrchestratorAgent (Gemini 2.5 Flash / Mock)
        6. PolicyAgent (Deterministic rules, hard floors, actuation)
        7. CloseoutAgent (Deterministic verdict persistence and telemetry emit)

    Args:
        profile_store: User baseline and profile storage port.
        ip_intel: IP intelligence and Tor exit node lookup port.
        actuator: Consequential action enforcement port.
        telemetry_sink: Event streaming and verdict storage port.
        settings: Engine configuration settings.

    Returns:
        Configured SequentialAgent tree.
    """
    engine_settings = settings or EngineSettings()

    intake = IntakeAgent(name="intake")
    enrichment = EnrichmentAgent(
        name="enrichment",
        profile_store=profile_store,
        ip_intel=ip_intel,
        actuator=actuator,
    )
    triage = TriageGate(name="triage")

    specialists = ParallelAgent(
        name="specialist_panel",
        sub_agents=[
            BehavioralAnalystAgent(name="behavioral_analyst", settings=engine_settings),
            ThreatIntelAgent(name="threat_intel", settings=engine_settings),
        ],
    )

    orchestrator = OrchestratorAgent(name="orchestrator", settings=engine_settings)
    policy = PolicyAgent(name="policy_agent", actuator=actuator)
    closeout = CloseoutAgent(
        name="closeout",
        telemetry_sink=telemetry_sink,
        settings=engine_settings,
    )

    return SequentialAgent(
        name="investigation_pipeline",
        sub_agents=[
            intake,
            enrichment,
            triage,
            specialists,
            orchestrator,
            policy,
            closeout,
        ],
    )
