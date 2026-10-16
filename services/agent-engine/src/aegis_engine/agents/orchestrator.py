"""OrchestratorAgent: Multi-agent synthesis, typology classification, and bounded adjustment."""

import os
import time
from collections.abc import AsyncGenerator

from aegis_common.logging import get_logger
from aegis_common.schemas.enums import TelemetryAction, Typology
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.verdict import ScoreBreakdown
from google import genai
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import (
    BehavioralReport,
    OrchestratorAssessment,
    ThreatReport,
)
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.agent.orchestrator")

MIN_SCORE_ADJUSTMENT: int = -10
MAX_SCORE_ADJUSTMENT: int = 10
ATO_BEHAVIORAL_SCORE_THRESHOLD: int = 30
CARD_TESTING_BURST_THRESHOLD: int = 5
DEVIATION_BEHAVIORAL_SCORE_THRESHOLD: int = 20


def create_deterministic_orchestrator_assessment(
    behavioral: BehavioralReport,
    threat: ThreatReport,
    features: FeatureVector,
    score_breakdown: ScoreBreakdown,
) -> OrchestratorAssessment:
    """Produce deterministic OrchestratorAssessment correlating specialist reports."""
    # 1. Account Takeover: Tor / VPN + Impossible Travel + New Device / Monetary Anomaly
    if (threat.is_tor or threat.is_impossible_travel) and (
        behavioral.behavioral_anomaly_score >= ATO_BEHAVIORAL_SCORE_THRESHOLD
        or features.device.is_new
    ):
        typology = Typology.ACCOUNT_TAKEOVER
        sp = features.travel.speed_kmh
        risk = behavioral.monetary_risk_level.lower()
        rationale = (
            f"Tor exit node connection and impossible travel velocity ({sp:.0f} km/h) "
            f"correlated with {risk} monetary deviation and new device. "
            f"High confidence Account Takeover pattern."
        )
        cited = ["ip.is_tor", "travel.speed_kmh", "monetary.z_score", "device.is_new"]
        adj = 0

    # 2. Structuring / Smurfing
    elif behavioral.is_structuring_suspected:
        typology = Typology.STRUCTURING
        count = features.velocity.near_threshold_count_15m
        rationale = (
            f"Multiple near-threshold transactions ({count}) in 15-minute "
            f"sliding window. High probability structuring smurfing pattern to "
            f"evade currency reporting."
        )
        cited = ["velocity.structuring_hit", "monetary.z_score"]
        adj = 0

    # 3. Card Testing / Velocity Burst
    elif features.velocity.count_60s >= CARD_TESTING_BURST_THRESHOLD:
        typology = Typology.CARD_TESTING
        burst = features.velocity.count_60s
        rationale = (
            f"Rapid velocity burst: {burst} transactions executed within 60 seconds. "
            f"Consistent with automated card testing or credential stuffing script."
        )
        cited = ["velocity.count_60s"]
        adj = 0

    # 4. Merchant Category Departure
    elif (
        features.category.is_novel
        and behavioral.behavioral_anomaly_score >= DEVIATION_BEHAVIORAL_SCORE_THRESHOLD
    ):
        typology = Typology.MERCHANT_DEVIATION
        rationale = (
            "Sudden transaction in novel merchant category with abnormal expenditure for baseline."
        )
        cited = ["category.is_novel", "monetary.z_score"]
        adj = 0

    # 5. Benign / Routine
    else:
        typology = Typology.NONE
        rationale = "Transaction metrics fall within acceptable baseline tolerance parameters."
        cited = []
        adj = 0

    return OrchestratorAssessment(
        typology=typology,
        rationale=rationale[:400],
        score_adjustment=adj,
        cited_evidence=cited,
    )


class OrchestratorAgent(BaseAgent):
    """Chief orchestrator synthesizing specialist reports into unified fraud typology."""

    def __init__(self, name: str = "orchestrator", settings: EngineSettings | None = None) -> None:
        super().__init__(name=name)
        self._settings = settings or EngineSettings()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Correlate specialist findings using Gemini or deterministic synthesis."""
        start_time = time.perf_counter()
        triage = ctx.session.state.get("triage", "INVESTIGATE")

        # Fast-Path: If clean, return immediate clean assessment
        if triage == "FAST_ALLOW":
            clean_assessment = OrchestratorAssessment(
                typology=Typology.NONE,
                rationale="Routine low-risk transaction. Consistent with historical profile.",
                score_adjustment=0,
                cited_evidence=[],
            )
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"orchestrator_assessment": clean_assessment}),
            )
            return

        behavioral: BehavioralReport = ctx.session.state["behavioral_report"]
        threat: ThreatReport = ctx.session.state["threat_report"]
        features: FeatureVector = ctx.session.state["features"]
        score_breakdown: ScoreBreakdown = ctx.session.state["score_breakdown"]
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        assessment: OrchestratorAssessment | None = None

        # Live Gemini LLM synthesis if configured and not in offline mock mode
        api_key = (
            self._settings.clean_gemini_api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        )
        if api_key and "\n" in api_key:
            parts = api_key.split()
            if len(parts) > 1 and all(p.isdigit() for p in parts):
                api_key = "".join(chr(int(p)) for p in parts)
        if not self._settings.is_mock_mode and api_key:
            try:
                client = genai.Client(api_key=api_key)
                prompt = (
                    "You are the Aegis Chief Fraud Orchestrator.\n"
                    "Synthesize the following specialist reports and verified score breakdown:\n"
                    "<behavioral_report>\n"
                    f"Monetary Risk: {behavioral.monetary_risk_level}\n"
                    f"Structuring: {behavioral.is_structuring_suspected}\n"
                    f"Findings: {'; '.join(behavioral.findings)}\n"
                    "</behavioral_report>\n"
                    "<threat_report>\n"
                    f"Network Risk: {threat.network_risk_level}\n"
                    f"Is Tor: {threat.is_tor}\n"
                    f"Impossible Travel: {threat.is_impossible_travel}\n"
                    f"Findings: {'; '.join(threat.findings)}\n"
                    "</threat_report>\n"
                    "<score_breakdown>\n"
                    f"Base: {score_breakdown.base}, Floor: {score_breakdown.floor}, "
                    f"Signals: {score_breakdown.signals}, Rules: {score_breakdown.rules}\n"
                    "</score_breakdown>\n"
                    "Task:\n"
                    "1. Determine primary typology ('NONE' | 'ACCOUNT_TAKEOVER' | "
                    "'STRUCTURING' | 'CARD_CLONING' | 'FRIENDLY_FRAUD')\n"
                    "2. Provide bounded score adjustment [-10, 10]\n"
                    "3. Write concise analyst rationale (max 400 chars) and list cited evidence.\n"
                    "Return strictly JSON with keys:\n"
                    "- typology\n"
                    "- rationale\n"
                    "- score_adjustment\n"
                    "- cited_evidence (list of strings)"
                )

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )

                logger.info(
                    "Invoking Gemini Orchestrator Synthesis",
                    model=self._settings.aegis_model_orchestrator,
                )
                resp = client.models.generate_content(
                    model=self._settings.aegis_model_orchestrator,
                    contents=prompt,
                    config=config,
                )
                if resp.text:
                    parsed = OrchestratorAssessment.model_validate_json(resp.text)
                    clamped_adj = max(
                        MIN_SCORE_ADJUSTMENT, min(MAX_SCORE_ADJUSTMENT, parsed.score_adjustment)
                    )
                    assessment = parsed.model_copy(update={"score_adjustment": clamped_adj})
                    logger.info(
                        "Gemini Orchestrator completed successfully",
                        typology=assessment.typology,
                        adjustment=clamped_adj,
                    )
            except Exception as exc:
                logger.warn("Gemini Orchestrator failed, using fallback", error=str(exc))
                assessment = None

        # Fallback to deterministic synthesis if mock or LLM failed
        if assessment is None:
            assessment = create_deterministic_orchestrator_assessment(
                behavioral, threat, features, score_breakdown
            )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        if emitter:
            adj_str = f"{assessment.score_adjustment:+d}"
            msg = (
                f"Synthesis: Typology={assessment.typology.value} (Adj: {adj_str}). "
                f"{assessment.rationale}"
            )
            is_crit = assessment.typology in [Typology.ACCOUNT_TAKEOVER, Typology.STRUCTURING]
            await emitter.emit(
                agent="Orchestrator",
                action=TelemetryAction.VERDICT,
                message=msg,
                severity="CRITICAL" if is_crit else "INFO",
                data={
                    "typology": assessment.typology.value,
                    "score_adjustment": assessment.score_adjustment,
                    "rationale": assessment.rationale,
                    "cited_evidence": assessment.cited_evidence,
                },
                latency_ms=latency_ms,
            )

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"orchestrator_assessment": assessment}),
        )
