"""Transaction intake endpoints for api-gateway."""

from typing import Annotated

from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict
from fastapi import APIRouter, Depends, Query, Response, status

from aegis_gateway.api.deps import get_gateway_service, verify_auth_or_mock
from aegis_gateway.application.gateway_service import GatewayService

router = APIRouter(tags=["transactions"])


@router.post(
    "/v1/transactions:analyze",
    response_model=Verdict | dict[str, str],
    summary="Submit transaction for multi-agent fraud investigation",
)
@router.post(
    "/api/analyze-tx",
    response_model=Verdict | dict[str, str],
    summary="Backward-compatible alias for transaction intake",
    include_in_schema=False,
)
async def analyze_transaction(
    tx: Transaction,
    response: Response,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
    mode: str = Query(default="sync", description="Execution mode: 'sync' or 'async'"),
) -> Verdict | dict[str, str]:
    """Ingest a payment transaction for multi-agent reasoning and deterministic
    policy evaluation.
    """
    result = await service.analyze_transaction(tx=tx, mode=mode)

    if isinstance(result, dict) and result.get("status") == "QUEUED":
        response.status_code = status.HTTP_202_ACCEPTED

    return result
