"""Hexagonal port protocol for user profile and historical baseline retrieval."""

from datetime import datetime
from typing import Any, Protocol

from aegis_common.schemas.features import UserBaseline


class ProfileStore(Protocol):
    """Port for retrieving hot-path user behavioral baselines and recent transactions."""

    async def get_baseline(self, user_id: str) -> UserBaseline:
        """Fetch 90-day statistical baseline for user.

        Args:
            user_id: Customer identifier.

        Returns:
            UserBaseline model (or cold-start default if not found).
        """
        ...

    async def get_recent_transactions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[tuple[datetime, float]]:
        """Fetch chronological list of recent (timestamp, amount) transactions from ring buffer.

        Args:
            user_id: Customer identifier.
            limit: Maximum transactions to retrieve.

        Returns:
            List of (timestamp, amount) tuples ordered chronologically.
        """
        ...

    async def get_last_transaction_location(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve coordinates, timestamp, and channel of user's most recent prior transaction.

        Args:
            user_id: Customer identifier.

        Returns:
            Dict containing lat, lon, ts, city, country, channel or None if first transaction.
        """
        ...

    async def is_known_device(self, user_id: str, device_id: str) -> bool:
        """Check if device identifier is present in user's recognized devices.

        Args:
            user_id: Customer identifier.
            device_id: Client device hash.

        Returns:
            True if recognized, False if novel device.
        """
        ...
