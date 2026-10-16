"""Unit tests for ActuatorService audit guarantees."""

from aegis_actuator.adapters.mock import (
    InMemoryAccountLedger,
    InMemoryAuditLog,
    InMemoryIdempotencyStore,
    LogNotifier,
)
from aegis_actuator.application.actions import ActuatorService
from aegis_actuator.domain.models import AuditAction


def _service() -> tuple[ActuatorService, InMemoryAuditLog]:
    audit = InMemoryAuditLog()
    service = ActuatorService(
        ledger=InMemoryAccountLedger(),
        audit_log=audit,
        notifier=LogNotifier(),
        idempotency=InMemoryIdempotencyStore(),
    )
    return service, audit


async def test_every_action_is_audited() -> None:
    service, audit = _service()
    await service.lock_account(
        user_id="USR_1", reason="H1", case_id="TX_0001", idempotency_key="k1", actor="engine"
    )
    await service.lock_account(
        user_id="USR_1", reason="H1", case_id="TX_0001", idempotency_key="k1", actor="engine"
    )
    await service.unlock_account(user_id="USR_1", reason="verified", actor="analyst")
    await service.block_transaction(tx_id="TX_0001", reason="H2", actor="engine")
    await service.dispatch_alert(user_id="USR_1", channel="SMS", message="m", actor="engine")

    assert [e.action for e in audit.entries] == [
        AuditAction.LOCK,
        AuditAction.LOCK_REPLAY,
        AuditAction.UNLOCK,
        AuditAction.BLOCK_TX,
        AuditAction.ALERT,
    ]
    assert audit.entries[2].actor == "analyst"
    assert audit.entries[2].case_id == "TX_0001"


async def test_failed_alert_is_audited_as_failure() -> None:
    class FailingNotifier:
        async def send(self, user_id: str, channel: str, message: str) -> bool:
            return False

    audit = InMemoryAuditLog()
    service = ActuatorService(
        ledger=InMemoryAccountLedger(),
        audit_log=audit,
        notifier=FailingNotifier(),
        idempotency=InMemoryIdempotencyStore(),
    )
    delivered = await service.dispatch_alert(
        user_id="USR_1", channel="SMS", message="m", actor="engine"
    )
    assert delivered is False
    assert audit.entries[-1].action == AuditAction.ALERT_FAILED
