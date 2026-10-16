"""Port for the append-only audit log."""

from typing import Protocol

from aegis_actuator.domain.models import AuditEntry


class AuditLogPort(Protocol):
    """Append-only sink for consequential-action audit records."""

    async def record(self, entry: AuditEntry) -> None:
        """Append an audit entry. Must not silently drop entries."""
        ...
