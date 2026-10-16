"""Main FastAPI entrypoint for actuator service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aegis_common.logging import configure_logging, get_logger
from fastapi import FastAPI
from pydantic import BaseModel

from aegis_actuator.api.errors import install_problem_handlers
from aegis_actuator.api.routes import router
from aegis_actuator.bootstrap import build_service
from aegis_actuator.settings import ActuatorSettings

logger = get_logger("aegis.actuator")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str


def create_app(settings: ActuatorSettings | None = None) -> FastAPI:
    """Create the actuator application. Adapters are built in the lifespan, not at import."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        resolved = settings or ActuatorSettings()
        configure_logging(log_level=resolved.aegis_log_level)
        app.state.settings = resolved
        app.state.service = build_service(resolved)
        logger.info(
            "Starting Aegis Actuator Service",
            env=resolved.aegis_env,
            adapter_mode=resolved.aegis_adapter_mode,
            notifier=resolved.aegis_notifier,
        )
        yield
        logger.info("Stopping Aegis Actuator Service")

    app = FastAPI(
        title="Aegis AI Fraud Ops - Actuator",
        description="Authorized consequential actions (lockout, block, alerts) execution",
        version="1.0.0",
        lifespan=lifespan,
    )
    install_problem_handlers(app)
    app.include_router(router)

    @app.get("/health", response_model=HealthResponse)
    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        """Liveness probe."""
        return HealthResponse(status="ok", service="aegis-actuator")

    @app.get("/readyz", response_model=HealthResponse)
    async def readyz() -> HealthResponse:
        """Readiness probe."""
        return HealthResponse(status="ready", service="aegis-actuator")

    return app


app = create_app()
