"""Mock TelemetrySink adapter buffering events and verdicts in memory."""

from collections import defaultdict

from aegis_common.logging import get_logger
from aegis_common.schemas.telemetry import TelemetryEvent
from aegis_common.schemas.verdict import Verdict

logger = get_logger("aegis.mock_telemetry")


class MockTelemetrySinkAdapter:
    """In-memory telemetry sink for testing investigation telemetry emissions."""

    def __init__(self) -> None:
        self.events: dict[str, list[TelemetryEvent]] = defaultdict(list)
        self.verdicts: dict[str, Verdict] = {}

    async def emit_event(self, tx_id: str, event: TelemetryEvent) -> None:
        """Buffer emitted event in chronological sequence."""
        self.events[tx_id].append(event)
        logger.info(
            "MOCK TELEMETRY: Event emitted",
            tx_id=tx_id,
            seq=event.seq,
            agent=event.agent,
            action=event.action,
            message=event.message,
        )

    async def save_verdict(self, verdict: Verdict) -> None:
        """Store verdict document in memory."""
        self.verdicts[verdict.tx_id] = verdict
        logger.info(
            "MOCK TELEMETRY: Verdict persisted",
            tx_id=verdict.tx_id,
            decision=verdict.decision,
            score=verdict.threat_score,
            risk_level=verdict.risk_level,
        )
