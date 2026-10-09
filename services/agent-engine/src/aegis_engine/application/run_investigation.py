"""Investigation use case wrapping Google ADK Runner with timeouts and degraded mode fallback."""

import asyncio
import time

from aegis_common.logging import get_logger
from aegis_common.schemas.enums import Decision, InvestigationStatus, Typology
from aegis_common.schemas.features import FeatureVector
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import (
    LatencyBreakdown,
    ModelVersions,
    ScoreBreakdown,
    Verdict,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from aegis_engine.agents.pipeline import build_investigation_pipeline
from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.policy import decide_action, map_score_to_risk_level
from aegis_engine.domain.scoring import compute_base_score
from aegis_engine.ports.actuator import ActuatorPort
from aegis_engine.ports.ip_intel import IpIntelPort
from aegis_engine.ports.profile_store import ProfileStore
from aegis_engine.ports.telemetry_sink import TelemetrySinkPort
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.application.investigation")


class InvestigationService:
    """Orchestrates end-to-end multi-agent fraud investigation with strict SLO enforcement."""

    def __init__(
        self,
        profile_store: ProfileStore,
        ip_intel: IpIntelPort,
        actuator: ActuatorPort,
        telemetry_sink: TelemetrySinkPort,
        settings: EngineSettings | None = None,
    ) -> None:
        self.profile_store = profile_store
        self.ip_intel = ip_intel
        self.actuator = actuator
        self.telemetry_sink = telemetry_sink
        self.settings = settings or EngineSettings()
        self.pipeline = build_investigation_pipeline(
            profile_store=self.profile_store,
            ip_intel=self.ip_intel,
            actuator=self.actuator,
            telemetry_sink=self.telemetry_sink,
            settings=self.settings,
        )
        self.session_service = InMemorySessionService()

    async def investigate(self, tx: Transaction) -> Verdict:
        """Execute the multi-agent investigation pipeline for an incoming transaction.

        Args:
            tx: Incoming Transaction to evaluate.

        Returns:
            Completed Verdict model.
        """
        start_time = time.perf_counter()
        emitter = TelemetryEmitter(tx_id=tx.tx_id, sink=self.telemetry_sink)
        timeout_sec = self.settings.aegis_timeout_pipeline_ms / 1000.0

        try:
            return await asyncio.wait_for(
                self._run_adk_pipeline(tx, emitter, start_time),
                timeout=timeout_sec,
            )
        except Exception as exc:
            logger.error(
                "ADK pipeline failed or timed out. Transitioning to Degraded Fallback",
                tx_id=tx.tx_id,
                error=str(exc),
            )
            return await self._execute_deterministic_degraded_fallback(
                tx=tx,
                start_time=start_time,
                error_msg=str(exc),
                emitter=emitter,
            )

    async def _run_adk_pipeline(
        self,
        tx: Transaction,
        emitter: TelemetryEmitter,
        start_time: float,
    ) -> Verdict:
        initial_state = {
            "tx": tx,
            "emitter": emitter,
            "profile_store": self.profile_store,
            "ip_intel": self.ip_intel,
            "actuator": self.actuator,
            "telemetry_sink": self.telemetry_sink,
            "pipeline_start_time": start_time,
            "degraded": False,
        }

        session = await self.session_service.create_session(
            app_name="aegis",
            user_id=tx.user_id,
            state=initial_state,
        )

        runner = Runner(
            agent=self.pipeline,
            app_name="aegis",
            session_service=self.session_service,
        )

        msg = types.Content(
            parts=[types.Part.from_text(text=f"Investigate transaction {tx.tx_id}")]
        )

        async for _event in runner.run_async(
            session_id=session.id,
            user_id=tx.user_id,
            new_message=msg,
        ):
            pass

        # Retrieve final verdict from session state
        updated_session = await self.session_service.get_session(
            app_name="aegis",
            user_id=tx.user_id,
            session_id=session.id,
        )
        if not updated_session or "verdict" not in updated_session.state:
            raise RuntimeError(
                f"Pipeline finished without producing a verdict in session: {session.id}"
            )

        verdict: Verdict = updated_session.state["verdict"]
        return verdict

    async def _execute_deterministic_degraded_fallback(
        self,
        tx: Transaction,
        start_time: float,
        error_msg: str,
        emitter: TelemetryEmitter,
    ) -> Verdict:
        """Pure deterministic fallback to guarantee a safe verdict when models fail or time out."""
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        # Build emergency fallback features
        features = FeatureVector()
        base_score, signals = compute_base_score(features, tx.merchant_category)
        risk_level = map_score_to_risk_level(base_score)
        decision, should_actuate, actuator_action = decide_action(risk_level)

        score_breakdown = ScoreBreakdown(
            base=base_score,
            floor=0,
            llm_adjustment=0,
            signals=signals,
            rules=[],
        )

        verdict = Verdict(
            tx_id=tx.tx_id,
            user_id=tx.user_id,
            status=InvestigationStatus.COMPLETED
            if decision == Decision.ALLOW
            else InvestigationStatus.ACTION_TAKEN,
            threat_score=base_score,
            risk_level=risk_level,
            decision=decision,
            should_actuate=should_actuate,
            typology=Typology.NONE,
            rationale=f"Deterministic degraded fallback active: {error_msg[:120]}",
            cited_evidence=[],
            score_breakdown=score_breakdown,
            actuator_action=actuator_action,
            latency_ms=LatencyBreakdown(total=elapsed_ms, enrichment=elapsed_ms),
            versions=ModelVersions(policy="1.0.0"),
            degraded=True,
            event_count=emitter.event_count,
        )

        await self.telemetry_sink.save_verdict(verdict)
        return verdict
