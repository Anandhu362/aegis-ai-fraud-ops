"""Mock Actuator adapter maintaining in-memory lockout and alert state."""

from aegis_common.logging import get_logger

logger = get_logger("aegis.mock_actuator")


class MockActuatorAdapter:
    """In-memory actuator adapter for offline execution and tests."""

    def __init__(self) -> None:
        self.locked_accounts: set[str] = set()
        self.blocked_transactions: set[str] = set()
        self.dispatched_alerts: list[dict[str, str]] = []

    async def execute_account_lockout(
        self,
        user_id: str,
        reason: str,
        case_id: str,
    ) -> bool:
        """Record account lockout in memory."""
        self.locked_accounts.add(user_id)
        logger.info(
            "MOCK ACTUATOR: Account locked",
            user_id=user_id,
            reason=reason,
            case_id=case_id,
        )
        return True

    async def block_transaction(self, tx_id: str, reason: str) -> bool:
        """Record transaction block in memory."""
        self.blocked_transactions.add(tx_id)
        logger.info("MOCK ACTUATOR: Transaction blocked", tx_id=tx_id, reason=reason)
        return True

    async def dispatch_alert(
        self,
        user_id: str,
        channel: str,
        message: str,
    ) -> bool:
        """Record dispatched alert in memory."""
        self.dispatched_alerts.append(
            {
                "user_id": user_id,
                "channel": channel,
                "message": message,
            }
        )
        logger.info(
            "MOCK ACTUATOR: Alert dispatched",
            user_id=user_id,
            channel=channel,
            message=message,
        )
        return True
