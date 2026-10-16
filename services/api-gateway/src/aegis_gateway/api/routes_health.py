"""Health check probes for api-gateway."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health status response."""

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
@router.get("/v1/health", response_model=HealthResponse)
@router.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok", service="aegis-gateway")


@router.get("/readyz", response_model=HealthResponse)
async def readyz() -> HealthResponse:
    """Readiness probe."""
    return HealthResponse(status="ready", service="aegis-gateway")
