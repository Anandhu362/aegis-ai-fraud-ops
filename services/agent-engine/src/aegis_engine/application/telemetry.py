"""Thread-safe telemetry event emitter for real-time investigation streaming."""

import asyncio
import time
from typing import Any

from aegis_common.schemas.enums import TelemetryAction
from aegis_common.schemas.telemetry import TelemetryEvent

from aegis_engine.ports.telemetry_sink import TelemetrySinkPort


class TelemetryEmitter:
    """Thread-safe monotonic telemetry event sequencer and dispatcher."""

    def __init__(self, tx_id: str, sink: TelemetrySinkPort) -> None:
        self.tx_id = tx_id
        self._sink = sink
        self._seq = 0
        self._lock = asyncio.Lock()
        self._events: list[TelemetryEvent] = []

    def __deepcopy__(self, memo: Any) -> "TelemetryEmitter":
        """Prevent ADK InMemorySessionService from cloning the live emitter."""
        return self

    @property
    def event_count(self) -> int:
        """Return the number of events emitted so far."""
        return self._seq

    @property
    def events(self) -> list[TelemetryEvent]:
        """Return a snapshot of all emitted events."""
        return list(self._events)

    async def emit(
        self,
        agent: str,
        action: TelemetryAction,
        message: str,
        severity: str = "INFO",
        data: dict[str, Any] | None = None,
        latency_ms: int = 0,
    ) -> TelemetryEvent:
        """Create, sequence, and stream a telemetry milestone.

        Args:
            agent: Emitting agent identifier (e.g., 'Intake', 'Threat Intel').
            action: Telemetry action classification.
            message: Human-readable terminal log line (masked for PII).
            severity: Event severity level ('INFO', 'WARN', 'CRITICAL').
            data: Structured payload or tool telemetry metrics.
            latency_ms: Execution duration in milliseconds.

        Returns:
            The created and persisted TelemetryEvent.
        """
        now_ms = int(time.time() * 1000)
        payload = data or {}

        async with self._lock:
            self._seq += 1
            event = TelemetryEvent(
                seq=self._seq,
                agent=agent,
                action=action,
                severity=severity,
                message=message[:240],
                data=payload,
                latency_ms=latency_ms,
                timestamp=now_ms,
            )
            self._events.append(event)

        # Dispatch asynchronously to the telemetry sink (Firestore or Mock)
        await self._sink.emit_event(self.tx_id, event)
        return event
