"""TriageGate: Sub-millisecond heuristic filter circuit breaker for clean transactions."""

from collections.abc import AsyncGenerator

from aegis_common.schemas.enums import TelemetryAction
from aegis_common.schemas.features import FeatureVector
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from aegis_engine.application.telemetry import TelemetryEmitter

MAX_CLEAN_Z_SCORE: float = 3.0
MAX_CLEAN_P95_RATIO: float = 2.0
MAX_CLEAN_ABUSE_SCORE: int = 20
MAX_CLEAN_SPEED_KMH: float = 120.0
MAX_CLEAN_COUNT_60S: int = 5
MAX_CLEAN_BASE_SCORE: int = 25
CRITICAL_BASE_SCORE_THRESHOLD: int = 70
ROUTINE_PURCHASE_MAX_AMOUNT: float = 100.0
ROUTINE_PURCHASE_MAX_Z_SCORE: float = 2.0
ROUTINE_PURCHASE_MAX_BASE_SCORE: int = 15


class TriageGate(BaseAgent):
    """Deterministic triage filter that short-circuits clean transactions to fast-path approval."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Evaluate if the transaction qualifies for the fast path, avoiding LLM calls.

        Args:
            ctx: ADK InvocationContext containing session state.

        Yields:
            Event with state_delta containing triage decision ('FAST_ALLOW' or 'INVESTIGATE').
        """
        features: FeatureVector = ctx.session.state["features"]
        base_score: int = ctx.session.state.get("base_after_rules", 0)
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        # Heuristic fast-path criteria
        is_clean_amount = (
            features.monetary.z_score < MAX_CLEAN_Z_SCORE
            and features.monetary.ratio_to_p95 < MAX_CLEAN_P95_RATIO
        )
        is_clean_network = (
            not features.ip.is_tor
            and not features.ip.is_vpn
            and features.ip.abuse_score < MAX_CLEAN_ABUSE_SCORE
        )
        is_clean_travel = (
            not features.travel.impossible and features.travel.speed_kmh <= MAX_CLEAN_SPEED_KMH
        )
        is_clean_velocity = (
            not features.velocity.structuring_hit
            and features.velocity.count_60s < MAX_CLEAN_COUNT_60S
            and not features.velocity.in_structuring_band
        )
        is_known_device = not features.device.is_new
        is_normal_category = not features.category.is_high_risk

        # In real-world banking, small routine retail purchases (< $100 or z <= 2.0)
        # on clean network and location do not get blocked by an unenrolled terminal ID.
        tx = ctx.session.state.get("transaction")
        tx_amount = float(getattr(tx, "amount", 0.0))
        is_routine_purchase = (
            tx_amount < ROUTINE_PURCHASE_MAX_AMOUNT
            or features.monetary.z_score <= ROUTINE_PURCHASE_MAX_Z_SCORE
        )
        device_acceptable = is_known_device or (
            is_routine_purchase and base_score <= ROUTINE_PURCHASE_MAX_BASE_SCORE
        )

        is_fast_allow = (
            base_score <= MAX_CLEAN_BASE_SCORE
            and is_clean_amount
            and is_clean_network
            and is_clean_travel
            and is_clean_velocity
            and device_acceptable
            and is_normal_category
        )

        triage_decision = "FAST_ALLOW" if is_fast_allow else "INVESTIGATE"

        if emitter:
            if is_fast_allow:
                await emitter.emit(
                    agent="Triage Gate",
                    action=TelemetryAction.THOUGHT,
                    message=f"Triage Fast-Path: Routine transaction (Score {base_score}). "
                    f"Skipping specialist panel. Fast approval granted.",
                    severity="INFO",
                    data={"triage": triage_decision, "score": base_score},
                )
            else:
                await emitter.emit(
                    agent="Triage Gate",
                    action=TelemetryAction.THOUGHT,
                    message=f"Triage: Risk signals detected (Base Score {base_score}). "
                    f"Escalating to Behavioral and Threat Intel specialist panel.",
                    severity="WARN" if base_score < CRITICAL_BASE_SCORE_THRESHOLD else "CRITICAL",
                    data={"triage": triage_decision, "score": base_score},
                )

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"triage": triage_decision}),
        )
