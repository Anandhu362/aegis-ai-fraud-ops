"""Hexagonal port protocol for real-time investigation telemetry and verdict storage."""

from typing import Protocol

from aegis_common.schemas.telemetry import TelemetryEvent
from aegis_common.schemas.verdict import Verdict


class TelemetrySinkPort(Protocol):
    """Port for streaming real-time milestones to Firestore and persisting verdicts."""

    async def emit_event(self, tx_id: str, event: TelemetryEvent) -> None:
        """Stream an ordered telemetry event milestone to the SOC terminal.

        Args:
            tx_id: Transaction identifier.
            event: Monotonically sequenced TelemetryEvent.
        """
        ...

    async def save_verdict(self, verdict: Verdict) -> None:
        """Persist the completed investigation verdict document.

        Args:
            verdict: Final Verdict model.
        """
        ...
