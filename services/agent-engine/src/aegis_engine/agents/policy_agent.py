"""PolicyAgent: Deterministic hard-rule enforcement, decision banding, and actuation."""

import time
from collections.abc import AsyncGenerator

from aegis_common.schemas.enums import Decision, TelemetryAction
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import ActuatorAction, ScoreBreakdown
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.domain.policy import decide_action, map_score_to_risk_level
from aegis_engine.domain.reports import OrchestratorAssessment
from aegis_engine.domain.scoring import apply_llm_adjustment
from aegis_engine.ports.actuator import ActuatorPort


class PolicyAgent(BaseAgent):
    """Deterministic policy agent applying hard-rule floors and authorized actions."""

    def __init__(self, name: str = "policy_agent", actuator: ActuatorPort | None = None) -> None:
        super().__init__(name=name)
        self._actuator = actuator

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Apply bounded adjustment, enforce hard floors, and actuate containment.

        Args:
            ctx: ADK InvocationContext containing session state.

        Yields:
            Event with state_delta containing final_score, decision, and actuator_action.
        """
        start_time = time.perf_counter()
        tx: Transaction = ctx.session.state["tx"]
        score_breakdown: ScoreBreakdown = ctx.session.state["score_breakdown"]
        base_after_rules: int = ctx.session.state.get("base_after_rules", score_breakdown.base)
        early_contained: bool = ctx.session.state.get("early_contained", False)
        assessment: OrchestratorAssessment | None = ctx.session.state.get("orchestrator_assessment")
        actuator = self._actuator or ctx.session.state.get("actuator")
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")

        llm_adj = assessment.score_adjustment if assessment else 0

        # 1. Enforce Bounded LLM Adjustment & Hard-Rule Floor Invariant
        final_score, effective_adj = apply_llm_adjustment(
            score_after_rules=base_after_rules,
            adjustment=llm_adj,
            hard_floor=score_breakdown.floor,
        )

        updated_breakdown = score_breakdown.model_copy(update={"llm_adjustment": effective_adj})

        # 2. Decision Banding
        risk_level = map_score_to_risk_level(final_score)
        decision, should_actuate, actuator_action = decide_action(
            risk_level=risk_level,
            is_early_containment=early_contained,
        )

        # 3. Consequential Actuation Enforcement
        if actuator and should_actuate:
            if decision == Decision.LOCK_ACCOUNT and not early_contained:
                typo_str = assessment.typology.value if assessment else "FRAUD"
                lock_msg = f"Aegis Critical Verdict: {typo_str}"
                await actuator.execute_account_lockout(
                    user_id=tx.user_id,
                    reason=lock_msg,
                    case_id=tx.tx_id,
                )
                await actuator.block_transaction(
                    tx_id=tx.tx_id,
                    reason=f"Declined: Account locked due to critical risk ({final_score}/100)",
                )
                alert_text = (
                    f"Security Alert: Your account was locked following an unauthorized "
                    f"transaction of ${float(tx.amount):.2f}."
                )
                await actuator.dispatch_alert(
                    user_id=tx.user_id,
                    channel="WHATSAPP",
                    message=alert_text,
                )
                actuator_action = ActuatorAction(
                    account_locked=True,
                    tx_blocked=True,
                    alert_dispatched=True,
                    dispatch_channel="WHATSAPP",
                    early_containment=early_contained,
                )

            elif decision == Decision.BLOCK_TX:
                block_reason = (
                    f"Declined: Transaction exceeds high risk policy threshold ({final_score}/100)"
                )
                await actuator.block_transaction(
                    tx_id=tx.tx_id,
                    reason=block_reason,
                )
                block_alert = (
                    f"Security Alert: Transaction of ${float(tx.amount):.2f} was declined "
                    f"due to security policy."
                )
                await actuator.dispatch_alert(
                    user_id=tx.user_id,
                    channel="WHATSAPP",
                    message=block_alert,
                )
                actuator_action = ActuatorAction(
                    account_locked=False,
                    tx_blocked=True,
                    alert_dispatched=True,
                    dispatch_channel="WHATSAPP",
                    early_containment=early_contained,
                )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # 4. Telemetry emission
        if emitter:
            action_summary = []
            if actuator_action.account_locked:
                action_summary.append("Account Locked")
            if actuator_action.tx_blocked:
                action_summary.append("Transaction Blocked")
            if actuator_action.alert_dispatched:
                action_summary.append("Customer Alerted")

            action_text = (
                f"Action: {', '.join(action_summary)}"
                if action_summary
                else "Action: None (Allowed)"
            )

            score_str = f"{final_score}/100"
            verdict_msg = (
                f"Verdict: {decision.value} (Score {score_str}, Band {risk_level.value}). "
                f"{action_text}."
            )
            await emitter.emit(
                agent="Policy Engine",
                action=TelemetryAction.ACTION if should_actuate else TelemetryAction.VERDICT,
                message=verdict_msg,
                severity="CRITICAL"
                if decision in [Decision.LOCK_ACCOUNT, Decision.BLOCK_TX]
                else "INFO",
                data={
                    "final_score": final_score,
                    "risk_level": risk_level.value,
                    "decision": decision.value,
                    "should_actuate": should_actuate,
                    "account_locked": actuator_action.account_locked,
                    "tx_blocked": actuator_action.tx_blocked,
                },
                latency_ms=latency_ms,
            )

        yield Event(
            author=self.name,
            actions=EventActions(
                state_delta={
                    "final_score": final_score,
                    "risk_level": risk_level,
                    "decision": decision,
                    "should_actuate": should_actuate,
                    "actuator_action": actuator_action,
                    "score_breakdown": updated_breakdown,
                }
            ),
        )
