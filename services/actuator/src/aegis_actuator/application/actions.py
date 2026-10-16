"""Actuator use cases: lock, unlock, block, alert — idempotent and fully audited."""

from datetime import UTC, datetime

from aegis_common.errors import AegisError, NotFoundError

from aegis_actuator.domain.models import AccountRecord, AuditAction, AuditEntry
from aegis_actuator.ports.audit_log import AuditLogPort
from aegis_actuator.ports.idempotency import IdempotencyStorePort
from aegis_actuator.ports.ledger import AccountLedgerPort
from aegis_actuator.ports.notifier import NotifierPort


class IdempotencyConflictError(AegisError):
    """Raised when an Idempotency-Key is reused for a different request."""

    status_code: int = 409
    error_type: str = "urn:aegis:error:idempotency-conflict"
    title: str = "Idempotency Key Conflict"


class LockOutcome:
    """Result of a lock request."""

    def __init__(self, record: AccountRecord, *, replayed: bool, already_locked: bool) -> None:
        self.record = record
        self.replayed = replayed
        self.already_locked = already_locked


class ActuatorService:
    """Executes consequential actions. Every attempt produces an audit entry."""

    def __init__(
        self,
        ledger: AccountLedgerPort,
        audit_log: AuditLogPort,
        notifier: NotifierPort,
        idempotency: IdempotencyStorePort,
    ) -> None:
        self._ledger = ledger
        self._audit = audit_log
        self._notifier = notifier
        self._idempotency = idempotency

    async def _audit_entry(
        self,
        action: AuditAction,
        *,
        actor: str,
        subject: str,
        reason: str,
        case_id: str | None = None,
    ) -> None:
        await self._audit.record(
            AuditEntry(
                action=action,
                actor=actor,
                subject=subject,
                reason=reason,
                case_id=case_id,
                at=datetime.now(UTC),
            )
        )

    async def lock_account(
        self,
        *,
        user_id: str,
        reason: str,
        case_id: str,
        idempotency_key: str,
        actor: str,
    ) -> LockOutcome:
        """Lock an account. Replays of the same Idempotency-Key never re-execute.

        Raises:
            IdempotencyConflictError: The key was already used for a different request.
        """
        fingerprint = f"lock:{user_id}:{case_id}"
        previous = await self._idempotency.get(idempotency_key)
        if previous is not None:
            stored_fingerprint, stored_record = previous
            if stored_fingerprint != fingerprint:
                raise IdempotencyConflictError(
                    "Idempotency-Key reused for a different request",
                    detail=f"Key {idempotency_key!r} was already used for another lock request",
                )
            await self._audit_entry(
                AuditAction.LOCK_REPLAY,
                actor=actor,
                subject=user_id,
                reason=reason,
                case_id=case_id,
            )
            return LockOutcome(stored_record, replayed=True, already_locked=True)

        existing = await self._ledger.get_account(user_id)
        if existing is not None and existing.locked:
            await self._idempotency.put(idempotency_key, fingerprint, existing)
            await self._audit_entry(
                AuditAction.LOCK_NOOP,
                actor=actor,
                subject=user_id,
                reason=reason,
                case_id=case_id,
            )
            return LockOutcome(existing, replayed=False, already_locked=True)

        record = await self._ledger.set_locked(user_id, locked=True, reason=reason, case_id=case_id)
        await self._idempotency.put(idempotency_key, fingerprint, record)
        await self._audit_entry(
            AuditAction.LOCK, actor=actor, subject=user_id, reason=reason, case_id=case_id
        )
        return LockOutcome(record, replayed=False, already_locked=False)

    async def unlock_account(self, *, user_id: str, reason: str, actor: str) -> AccountRecord:
        """Unlock an account (analyst override). Idempotent if already unlocked.

        Raises:
            NotFoundError: The account has no ledger record.
        """
        existing = await self._ledger.get_account(user_id)
        if existing is None:
            raise NotFoundError(
                "Account not found", detail=f"No ledger record for account {user_id}"
            )
        if not existing.locked:
            await self._audit_entry(
                AuditAction.UNLOCK_NOOP, actor=actor, subject=user_id, reason=reason
            )
            return existing
        record = await self._ledger.set_locked(
            user_id, locked=False, reason=reason, case_id=existing.case_id
        )
        await self._audit_entry(
            AuditAction.UNLOCK,
            actor=actor,
            subject=user_id,
            reason=reason,
            case_id=existing.case_id,
        )
        return record

    async def get_account(self, user_id: str) -> AccountRecord:
        """Return account state.

        Raises:
            NotFoundError: The account has no ledger record.
        """
        record = await self._ledger.get_account(user_id)
        if record is None:
            raise NotFoundError(
                "Account not found", detail=f"No ledger record for account {user_id}"
            )
        return record

    async def block_transaction(self, *, tx_id: str, reason: str, actor: str) -> bool:
        """Block a transaction. Returns True if newly blocked, False if already blocked."""
        newly_blocked = await self._ledger.block_transaction(tx_id, reason)
        await self._audit_entry(
            AuditAction.BLOCK_TX if newly_blocked else AuditAction.BLOCK_TX_NOOP,
            actor=actor,
            subject=tx_id,
            reason=reason,
            case_id=tx_id,
        )
        return newly_blocked

    async def dispatch_alert(self, *, user_id: str, channel: str, message: str, actor: str) -> bool:
        """Dispatch a customer alert. Failures are audited and reported, not hidden."""
        delivered = await self._notifier.send(user_id, channel, message)
        await self._audit_entry(
            AuditAction.ALERT if delivered else AuditAction.ALERT_FAILED,
            actor=actor,
            subject=user_id,
            reason=f"alert via {channel}",
        )
        return delivered
