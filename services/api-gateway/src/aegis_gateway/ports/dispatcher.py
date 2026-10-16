"""Hexagonal port protocol for dispatching transactions to agent-engine."""

from typing import Protocol

from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict


class InvestigationDispatcherPort(Protocol):
    """Port for sending transactions to agent-engine via HTTP sync or Pub/Sub async."""

    async def dispatch_sync(self, tx: Transaction) -> Verdict:
        """Synchronously investigate transaction and await completed verdict."""
        ...

    async def dispatch_async(self, tx: Transaction) -> dict[str, str]:
        """Asynchronously publish transaction for background multi-agent investigation."""
        ...
