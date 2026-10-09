"""Main FastAPI entrypoint for actuator service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aegis_common.logging import configure_logging, get_logger
from fastapi import FastAPI
from pydantic import BaseModel

from aegis_actuator.settings import ActuatorSettings

logger = get_logger("aegis.actuator")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Actuator lifespan."""
    settings = ActuatorSettings()
    configure_logging(log_level=settings.aegis_log_level)
    logger.info(
        "Starting Aegis Actuator Service",
        env=settings.aegis_env,
        notifier=settings.aegis_notifier,
        port=settings.aegis_port,
    )
    yield
    logger.info("Stopping Aegis Actuator Service")


app = FastAPI(
    title="Aegis AI Fraud Ops - Actuator",
    description="Authorized consequential actions (lockout, block, alerts) execution",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok", service="aegis-actuator")


@app.get("/readyz", response_model=HealthResponse)
async def readyz() -> HealthResponse:
    """Readiness probe."""
    return HealthResponse(status="ready", service="aegis-actuator")
