"""Main FastAPI entrypoint for agent-engine service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aegis_common.logging import configure_logging, get_logger
from fastapi import FastAPI
from pydantic import BaseModel

from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.engine")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan setup."""
    settings = EngineSettings()
    configure_logging(log_level=settings.aegis_log_level)
    logger.info(
        "Starting Aegis Agent Engine",
        env=settings.aegis_env,
        adapter_mode=settings.aegis_adapter_mode,
        orchestrator_model=settings.aegis_model_orchestrator,
        specialist_model=settings.aegis_model_specialist,
    )
    yield
    logger.info("Stopping Aegis Agent Engine")


app = FastAPI(
    title="Aegis AI Fraud Ops - Agent Engine",
    description="Google ADK multi-agent pipeline and Gemini investigation engine",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/healthz", response_model=HealthResponse)
async def healthz() -> HealthResponse:
    """Liveness probe."""
    return HealthResponse(status="ok", service="aegis-engine")


@app.get("/readyz", response_model=HealthResponse)
async def readyz() -> HealthResponse:
    """Readiness probe."""
    return HealthResponse(status="ready", service="aegis-engine")
