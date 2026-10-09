"""IntakeAgent: Gateway validation and prompt-injection sanitization."""

import re
from collections.abc import AsyncGenerator

from aegis_common.schemas.enums import TelemetryAction
from aegis_common.schemas.transaction import Transaction
from google.adk.agents import BaseAgent, InvocationContext
from google.adk.events import Event, EventActions

from aegis_engine.application.telemetry import TelemetryEmitter


class IntakeAgent(BaseAgent):
    """Deterministic intake agent performing schema validation and prompt sanitization."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        """Validate transaction boundaries, sanitize untrusted fields, and emit opening thought.

        Args:
            ctx: ADK InvocationContext containing session state.

        Yields:
            Event with state_delta containing sanitized transaction.
        """
        raw_tx = ctx.session.state.get("tx")
        if isinstance(raw_tx, dict):
            tx = Transaction.model_validate(raw_tx)
        elif isinstance(raw_tx, Transaction):
            tx = raw_tx
        else:
            raise ValueError(f"IntakeAgent: Missing or invalid 'tx' in session state: {raw_tx}")

        # Strip control characters from untrusted merchant description
        sanitized_merchant = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", tx.merchant).strip()[:120]
        sanitized_tx = tx.model_copy(update={"merchant": sanitized_merchant})

        # Telemetry: emit opening investigation thought
        emitter: TelemetryEmitter | None = ctx.session.state.get("emitter")
        if emitter:
            await emitter.emit(
                agent="Intake",
                action=TelemetryAction.THOUGHT,
                message=(
                    f"Received transaction {sanitized_tx.tx_id} "
                    f"(${float(sanitized_tx.amount):.2f} at '{sanitized_merchant}'). "
                    f"Initiating multi-signal investigation."
                ),
                severity="INFO",
                data={
                    "tx_id": sanitized_tx.tx_id,
                    "user_id": sanitized_tx.user_id,
                    "amount": float(sanitized_tx.amount),
                    "channel": sanitized_tx.channel.value,
                },
            )

        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"tx": sanitized_tx}),
        )
