"""Hexagonal port protocol for caching and retrieving investigation cases."""

import asyncio
from typing import Protocol

from aegis_common.schemas.verdict import AnalystDecision, Verdict


class CaseRepositoryPort(Protocol):
    """Port for storing and retrieving transaction investigation cases."""

    async def get_verdict(self, tx_id: str) -> Verdict | None:
        """Retrieve stored verdict for a transaction ID."""
        ...

    async def save_verdict(self, verdict: Verdict) -> None:
        """Store verdict document."""
        ...

    async def has_transaction(self, tx_id: str) -> bool:
        """Return True if transaction ID has already been ingested (idempotency check)."""
        ...

    async def record_analyst_decision(
        self,
        tx_id: str,
        decision: AnalystDecision,
    ) -> Verdict | None:
        """Attach human analyst decision override to case."""
        ...

    async def get_metrics_summary(self) -> dict[str, object]:
        """Compute aggregate system KPI metrics."""
        ...

    async def list_verdicts(self, limit: int = 50) -> list[Verdict]:
        """Retrieve recent investigation verdicts."""
        ...

    async def subscribe(self) -> asyncio.Queue[Verdict | None]:
        """Subscribe to live real-time verdict events."""
        ...

    async def unsubscribe(self, queue: asyncio.Queue[Verdict | None]) -> None:
        """Unsubscribe queue from live events."""
        ...

    async def clear(self) -> int:
        """Purge all stored/cached verdicts and notify listeners."""
        ...

