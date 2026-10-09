"""CloseoutAgent: Telemetry flush, verdict document persistence, and deep review trigger."""

import time
from collections.abc import AsyncGenerator

from aegis_common.schemas.enums import Decision, InvestigationStatus, Typology
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import (
    ActuatorAction,
    LatencyBreakdown,
    ModelVersions,
    ScoreBreakdown,
    Verdict,
)
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.reports import OrchestratorAssessment
from aegis_engine.ports.telemetry_sink import TelemetrySinkPort
from aegis_engine.settings import EngineSettings


class CloseoutAgent(BaseAgent):
    """Deterministic closeout agent assembling the final Verdict and saving to telemetry sink."""

    def __init__(
        self,
        name: str = "closeout",
        telemetry_sink: TelemetrySinkPort | None = None,
        settings: EngineSettings | None = None,
    ) -> None:
        super().__init__(name=name)
        self._telemetry_sink = telemetry_sink
        self._settings = settings or EngineSettings()

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Assemble Verdict, persist to Firestore, and finalize telemetry streaming.

        Args:
            ctx: ADK InvocationContext containing session state.

        Yields:
            Event with state_delta containing the finalized Verdict.
        """
        tx: Transaction = ctx.session.state["tx"]
        final_score: int = ctx.session.state["final_score"]
        risk_level = ctx.session.state["risk_level"]
        decision: Decision = ctx.session.state["decision"]
        should_actuate: bool = ctx.session.state.get("should_actuate", False)
        actuator_action: ActuatorAction = ctx.session.state.get("actuator_action", ActuatorAction())
        score_breakdown: ScoreBreakdown = ctx.session.state["score_breakdown"]
        assessment: OrchestratorAssessment | None = ctx.session.state.get("orchestrator_assessment")
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")
        telemetry_sink = self._telemetry_sink or ctx.session.state.get("telemetry_sink")

        # Map investigation status
        if decision in [Decision.LOCK_ACCOUNT, Decision.BLOCK_TX]:
            status = InvestigationStatus.ACTION_TAKEN
        else:
            status = InvestigationStatus.COMPLETED

        typology = assessment.typology if assessment else Typology.NONE
        rationale = (
            assessment.rationale if assessment else "Transaction permitted under standard policy."
        )
        cited_evidence = assessment.cited_evidence if assessment else []

        enrichment_latency = ctx.session.state.get("enrichment_latency_ms", 0)
        policy_latency = ctx.session.state.get("policy_latency_ms", 0)
        pipeline_start = ctx.session.state.get("pipeline_start_time", time.perf_counter())
        total_latency = int((time.perf_counter() - pipeline_start) * 1000)

        latency = LatencyBreakdown(
            total=total_latency,
            enrichment=enrichment_latency,
            specialists=max(0, total_latency - enrichment_latency - policy_latency),
            orchestrator=0,
            policy=policy_latency,
        )

        versions = ModelVersions(
            policy="1.0.0",
            orchestrator={
                "model": self._settings.aegis_model_orchestrator,
                "prompt": "1.0.0",
            },
            specialist={
                "model": self._settings.aegis_model_specialist,
                "prompt": "1.0.0",
            },
        )

        event_count = emitter.event_count if emitter else 0

        verdict = Verdict(
            tx_id=tx.tx_id,
            user_id=tx.user_id,
            status=status,
            threat_score=final_score,
            risk_level=risk_level,
            decision=decision,
            should_actuate=should_actuate,
            typology=typology,
            rationale=rationale,
            cited_evidence=cited_evidence,
            score_breakdown=score_breakdown,
            actuator_action=actuator_action,
            latency_ms=latency,
            versions=versions,
            degraded=ctx.session.state.get("degraded", False),
            event_count=event_count,
        )

        # Save to telemetry sink (Firestore or Mock)
        if telemetry_sink:
            await telemetry_sink.save_verdict(verdict)

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"verdict": verdict}),
        )
