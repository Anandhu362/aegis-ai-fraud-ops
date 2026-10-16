"""Mock dispatcher executing InvestigationService directly in-process for standalone testing."""

import asyncio

from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict
from aegis_engine.bootstrap import build_engine
from aegis_engine.settings import EngineSettings


class MockInvestigationDispatcher:
    """In-process dispatcher executing the ADK pipeline without network hops."""

    def __init__(self, settings: EngineSettings | None = None) -> None:
        engine_settings = settings or EngineSettings()
        self.container = build_engine(engine_settings)
        self._background_tasks: set[asyncio.Task[Verdict]] = set()

    async def dispatch_sync(self, tx: Transaction) -> Verdict:
        """Run in-process investigation pipeline."""
        return await self.container.service.investigate(tx)

    async def dispatch_async(self, tx: Transaction) -> dict[str, str]:
        """Fire investigation in background and immediately return queued state."""
        task = asyncio.create_task(self.container.service.investigate(tx))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return {
            "tx_id": tx.tx_id,
            "status": "QUEUED",
            "status_url": f"/v1/investigations/{tx.tx_id}",
        }
