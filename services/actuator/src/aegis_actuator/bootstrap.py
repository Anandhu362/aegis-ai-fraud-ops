"""Composition root for the actuator service."""

from aegis_actuator.adapters.mock import (
    InMemoryAccountLedger,
    InMemoryAuditLog,
    InMemoryIdempotencyStore,
    LogNotifier,
)
from aegis_actuator.application.actions import ActuatorService
from aegis_actuator.settings import ActuatorSettings


def build_service(settings: ActuatorSettings) -> ActuatorService:
    """Build the ActuatorService for the configured adapter mode.

    Raises:
        RuntimeError: For adapter modes without an implementation (fail closed at startup).
    """
    if settings.aegis_adapter_mode not in ("mock", "gcp"):
        raise RuntimeError(f"Adapter mode {settings.aegis_adapter_mode!r} is not implemented")
    if settings.aegis_notifier != "log":
        raise RuntimeError(f"Notifier {settings.aegis_notifier!r} is not implemented; use 'log'")
    return ActuatorService(
        ledger=InMemoryAccountLedger(),
        audit_log=InMemoryAuditLog(),
        notifier=LogNotifier(),
        idempotency=InMemoryIdempotencyStore(),
    )
