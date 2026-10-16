"""Actuator routes (spec 06 §4 'actuator (internal)')."""

from datetime import datetime
from typing import Annotated

from aegis_common.schemas.enums import DispatchChannel
from fastapi import APIRouter, Depends, Header, Path
from pydantic import BaseModel, ConfigDict, Field

from aegis_actuator.api.deps import get_service, require_caller
from aegis_actuator.application.actions import ActuatorService
from aegis_actuator.domain.models import AccountRecord

router = APIRouter(prefix="/v1")

UserIdPath = Annotated[str, Path(pattern=r"^USR_[A-Z0-9]{2,32}$")]
TxIdPath = Annotated[str, Path(pattern=r"^TX_[A-Z0-9]{4,32}$")]
Caller = Annotated[str, Depends(require_caller)]
Service = Annotated[ActuatorService, Depends(get_service)]


class LockRequest(BaseModel):
    """Body for an account lock."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=500)
    case_id: str = Field(pattern=r"^TX_[A-Z0-9]{4,32}$")


class UnlockRequest(BaseModel):
    """Body for an analyst unlock; a reason is mandatory."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=3, max_length=500)


class BlockRequest(BaseModel):
    """Body for a transaction block."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1, max_length=500)


class AlertRequest(BaseModel):
    """Body for a customer alert."""

    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$")
    channel: DispatchChannel
    message: str = Field(min_length=1, max_length=1000)


class AccountResponse(BaseModel):
    """Account lock state."""

    user_id: str
    locked: bool
    reason: str | None
    case_id: str | None
    updated_at: datetime
    replayed: bool = False
    already_locked: bool = False

    @classmethod
    def from_record(
        cls, record: AccountRecord, *, replayed: bool = False, already_locked: bool = False
    ) -> "AccountResponse":
        """Build from a domain record."""
        return cls(
            user_id=record.user_id,
            locked=record.locked,
            reason=record.reason,
            case_id=record.case_id,
            updated_at=record.updated_at,
            replayed=replayed,
            already_locked=already_locked,
        )


class BlockResponse(BaseModel):
    """Transaction block result."""

    tx_id: str
    blocked: bool
    newly_blocked: bool


class AlertResponse(BaseModel):
    """Alert dispatch result."""

    user_id: str
    channel: DispatchChannel
    delivered: bool


@router.post("/accounts/{user_id}:lock", response_model=AccountResponse)
async def lock_account(
    user_id: UserIdPath,
    body: LockRequest,
    service: Service,
    caller: Caller,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
) -> AccountResponse:
    """Lock an account. `Idempotency-Key` header is required."""
    outcome = await service.lock_account(
        user_id=user_id,
        reason=body.reason,
        case_id=body.case_id,
        idempotency_key=idempotency_key,
        actor=caller,
    )
    return AccountResponse.from_record(
        outcome.record, replayed=outcome.replayed, already_locked=outcome.already_locked
    )


@router.post("/accounts/{user_id}:unlock", response_model=AccountResponse)
async def unlock_account(
    user_id: UserIdPath, body: UnlockRequest, service: Service, caller: Caller
) -> AccountResponse:
    """Analyst unlock; reason required."""
    record = await service.unlock_account(user_id=user_id, reason=body.reason, actor=caller)
    return AccountResponse.from_record(record)


@router.get("/accounts/{user_id}", response_model=AccountResponse)
async def get_account(user_id: UserIdPath, service: Service, _caller: Caller) -> AccountResponse:
    """Return current account lock state."""
    return AccountResponse.from_record(await service.get_account(user_id))


@router.post("/transactions/{tx_id}:block", response_model=BlockResponse)
async def block_transaction(
    tx_id: TxIdPath, body: BlockRequest, service: Service, caller: Caller
) -> BlockResponse:
    """Decline a transaction (idempotent)."""
    newly = await service.block_transaction(tx_id=tx_id, reason=body.reason, actor=caller)
    return BlockResponse(tx_id=tx_id, blocked=True, newly_blocked=newly)


@router.post("/alerts", response_model=AlertResponse)
async def dispatch_alert(body: AlertRequest, service: Service, caller: Caller) -> AlertResponse:
    """Dispatch a customer security alert."""
    delivered = await service.dispatch_alert(
        user_id=body.user_id, channel=body.channel.value, message=body.message, actor=caller
    )
    return AlertResponse(user_id=body.user_id, channel=body.channel, delivered=delivered)
