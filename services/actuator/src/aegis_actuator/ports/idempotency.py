"""Port for idempotency-key storage."""

from typing import Protocol

from aegis_actuator.domain.models import AccountRecord


class IdempotencyStorePort(Protocol):
    """Maps Idempotency-Key -> (request fingerprint, stored result)."""

    async def get(self, key: str) -> tuple[str, AccountRecord] | None:
        """Return (fingerprint, result) for a previously seen key, else None."""
        ...

    async def put(self, key: str, fingerprint: str, result: AccountRecord) -> None:
        """Store the result for a key."""
        ...
