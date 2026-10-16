"""Deterministic in-memory adapters for offline (AEGIS_ADAPTER_MODE=mock) operation and tests."""

import asyncio
from datetime import UTC, datetime

from aegis_common.logging import get_logger

from aegis_actuator.domain.models import AccountRecord, AuditEntry

logger = get_logger("aegis.actuator.mock")


class InMemoryAccountLedger:
    """In-memory account and transaction ledger."""

    def __init__(self) -> None:
        self._accounts: dict[str, AccountRecord] = {}
        self._blocked: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def get_account(self, user_id: str) -> AccountRecord | None:
        """Return the account record if present."""
        return self._accounts.get(user_id)

    async def set_locked(
        self,
        user_id: str,
        *,
        locked: bool,
        reason: str,
        case_id: str | None,
    ) -> AccountRecord:
        """Set the lock state."""
        async with self._lock:
            record = AccountRecord(
                user_id=user_id,
                locked=locked,
                reason=reason,
                case_id=case_id,
                updated_at=datetime.now(UTC),
            )
            self._accounts[user_id] = record
            return record

    async def block_transaction(self, tx_id: str, reason: str) -> bool:
        """Block a transaction; False if it was already blocked."""
        async with self._lock:
            if tx_id in self._blocked:
                return False
            self._blocked[tx_id] = reason
            return True

    async def is_blocked(self, tx_id: str) -> bool:
        """Return True if blocked."""
        return tx_id in self._blocked


class InMemoryAuditLog:
    """Append-only in-memory audit log."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    async def record(self, entry: AuditEntry) -> None:
        """Append an entry and mirror it to structured logs."""
        self.entries.append(entry)
        logger.info(
            "AUDIT",
            action=entry.action,
            actor=entry.actor,
            subject=entry.subject,
            case_id=entry.case_id,
        )


class LogNotifier:
    """Notifier that writes alerts to structured logs only (AEGIS_NOTIFIER=log)."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str]] = []

    async def send(self, user_id: str, channel: str, message: str) -> bool:
        """Record the alert; message body is not logged to avoid leaking content."""
        self.sent.append((user_id, channel, message))
        logger.info("ALERT (log notifier)", user_id=user_id, channel=channel, length=len(message))
        return True


class InMemoryIdempotencyStore:
    """In-memory Idempotency-Key store."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[str, AccountRecord]] = {}

    async def get(self, key: str) -> tuple[str, AccountRecord] | None:
        """Return stored entry for key."""
        return self._items.get(key)

    async def put(self, key: str, fingerprint: str, result: AccountRecord) -> None:
        """Store entry for key."""
        self._items[key] = (fingerprint, result)
