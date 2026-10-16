"""Port for the account/transaction ledger (core-banking stand-in)."""

from typing import Protocol

from aegis_actuator.domain.models import AccountRecord


class AccountLedgerPort(Protocol):
    """Persists account lock state and blocked transactions."""

    async def get_account(self, user_id: str) -> AccountRecord | None:
        """Return the account record, or None if the account has never been actioned."""
        ...

    async def set_locked(
        self,
        user_id: str,
        *,
        locked: bool,
        reason: str,
        case_id: str | None,
    ) -> AccountRecord:
        """Set the lock state and return the updated record."""
        ...

    async def block_transaction(self, tx_id: str, reason: str) -> bool:
        """Mark a transaction blocked. Returns True if newly blocked, False if already blocked."""
        ...

    async def is_blocked(self, tx_id: str) -> bool:
        """Return True if the transaction is blocked."""
        ...
