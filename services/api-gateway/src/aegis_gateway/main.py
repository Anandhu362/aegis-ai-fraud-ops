"""Main FastAPI entrypoint for aegis-gateway."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aegis_common.errors import AegisError
from aegis_common.logging import configure_logging, get_logger
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from aegis_gateway.api.routes_health import router as health_router
from aegis_gateway.settings import GatewaySettings

logger = get_logger("aegis.gateway")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown."""
    settings = GatewaySettings()
    configure_logging(log_level=settings.aegis_log_level)
    logger.info(
        "Starting Aegis API Gateway",
        env=settings.aegis_env,
        adapter_mode=settings.aegis_adapter_mode,
        port=settings.aegis_port,
    )
    yield
    logger.info("Stopping Aegis API Gateway")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Aegis AI Fraud Ops - API Gateway",
        description="Edge transaction intake, validation, and dispatch service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register error handlers for RFC 7807 problem details
    @app.exception_handler(AegisError)
    async def aegis_error_handler(request: Request, exc: AegisError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem_details(instance=str(request.url)),
            headers={"Content-Type": "application/problem+json"},
        )

    # Include routers
    app.include_router(health_router)

    return app


app = create_app()
