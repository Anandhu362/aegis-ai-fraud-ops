"""Pure domain models for the actuator service (no I/O, no framework imports)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class AuditAction(StrEnum):
    """Consequential action categories recorded in the audit log."""

    LOCK = "LOCK"
    LOCK_NOOP = "LOCK_NOOP"
    LOCK_REPLAY = "LOCK_REPLAY"
    UNLOCK = "UNLOCK"
    UNLOCK_NOOP = "UNLOCK_NOOP"
    BLOCK_TX = "BLOCK_TX"
    BLOCK_TX_NOOP = "BLOCK_TX_NOOP"
    ALERT = "ALERT"
    ALERT_FAILED = "ALERT_FAILED"


class AccountRecord(BaseModel):
    """Current lock state of a customer account."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    locked: bool
    reason: str | None = None
    case_id: str | None = None
    updated_at: datetime


class AuditEntry(BaseModel):
    """Immutable audit record for every consequential action attempt."""

    model_config = ConfigDict(frozen=True)

    action: AuditAction
    actor: str = Field(description="Authenticated caller identity")
    subject: str = Field(description="user_id or tx_id the action targeted")
    reason: str
    case_id: str | None = None
    at: datetime
