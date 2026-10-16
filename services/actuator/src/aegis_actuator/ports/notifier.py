"""Port for customer security notifications."""

from typing import Protocol


class NotifierPort(Protocol):
    """Delivers customer-facing security alerts."""

    async def send(self, user_id: str, channel: str, message: str) -> bool:
        """Send an alert. Returns True on accepted delivery."""
        ...
