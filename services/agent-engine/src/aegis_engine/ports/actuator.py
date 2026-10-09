"""Hexagonal port protocol for executing consequential containment actions."""

from typing import Protocol


class ActuatorPort(Protocol):
    """Port for dispatching authorized account lockouts, transaction blocks, and alerts."""

    async def execute_account_lockout(
        self,
        user_id: str,
        reason: str,
        case_id: str,
    ) -> bool:
        """Execute core-banking account lockout.

        Args:
            user_id: Customer account identifier.
            reason: Explanatory audit justification.
            case_id: Investigation transaction ID.

        Returns:
            True if successfully executed, False otherwise.
        """
        ...

    async def block_transaction(self, tx_id: str, reason: str) -> bool:
        """Decline/block an in-flight payment transaction.

        Args:
            tx_id: Transaction identifier.
            reason: Decline rationale.

        Returns:
            True if block was registered.
        """
        ...

    async def dispatch_alert(
        self,
        user_id: str,
        channel: str,
        message: str,
    ) -> bool:
        """Dispatch external security notification (WhatsApp, SMS, etc).

        Args:
            user_id: Customer identifier.
            channel: Notification channel.
            message: Formatted security alert content.

        Returns:
            True if dispatched.
        """
        ...
