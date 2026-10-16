"""Metrics summary endpoints for SOC dashboard health and KPIs."""

from typing import Annotated

from fastapi import APIRouter, Depends

from aegis_gateway.api.deps import get_gateway_service, verify_auth_or_mock
from aegis_gateway.application.gateway_service import GatewayService

router = APIRouter(prefix="/v1/metrics", tags=["metrics"])


@router.get(
    "",
    summary="Get aggregated SOC operational KPIs",
)
@router.get(
    "/summary",
    summary="Get aggregated SOC operational KPIs",
)
async def get_metrics_summary(
    service: Annotated[GatewayService, Depends(get_gateway_service)],
    _caller: Annotated[str, Depends(verify_auth_or_mock)],
) -> dict[str, object]:
    """Retrieve operational metrics: total processed, blocked count, protected funds,
    and average latency.
    """
    return await service.get_metrics_summary()

