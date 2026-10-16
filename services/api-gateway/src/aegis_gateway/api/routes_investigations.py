"""Investigation case snapshot and analyst decision endpoints."""

from typing import Annotated

from aegis_common.schemas.verdict import AnalystDecision, Verdict
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from aegis_gateway.api.deps import get_gateway_service, verify_auth_or_mock
from aegis_gateway.application.gateway_service import GatewayService

router = APIRouter(prefix="/v1/investigations", tags=["investigations"])


@router.get(
    "",
    response_model=list[Verdict],
    summary="List recent investigation cases for the live SOC dashboard feed",
)
async def list_investigations(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
    limit: int = 50,
) -> list[Verdict]:
    """Retrieve recent investigation verdicts for the live ingestion stream."""
    return await service.list_investigations(limit=limit)


@router.get(
    "/stream",
    summary="Real-time Server-Sent Events (SSE) investigation stream",
)
async def stream_investigations(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
) -> StreamingResponse:
    """Stream newly evaluated verdicts and analyst decisions in real time."""
    return StreamingResponse(
        service.stream_investigations(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{tx_id}",
    response_model=Verdict,
    summary="Get investigation case snapshot and final verdict",
)
async def get_investigation(
    tx_id: str,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
) -> Verdict:
    """Retrieve the synthesized verdict and explanation for a transaction ID."""
    return await service.get_investigation(tx_id)


@router.post(
    "/{tx_id}/decision",
    response_model=Verdict,
    summary="Record human fraud analyst override decision",
)
async def record_decision(
    tx_id: str,
    decision: AnalystDecision,
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
) -> Verdict:
    """Record an audited manual decision (APPROVE, CONFIRM_FRAUD, or UNLOCK) for a case."""
    return await service.record_analyst_decision(tx_id=tx_id, decision=decision)


@router.post(
    ":clear",
    summary="Purge past investigation cases and reset live dashboard",
)
@router.delete(
    "",
    summary="Purge past investigation cases and reset live dashboard",
)
async def clear_investigations(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
) -> dict[str, object]:
    """Purge stored investigations and hot cache, resetting the SOC dashboard to clean state."""
    return await service.clear_investigations()
