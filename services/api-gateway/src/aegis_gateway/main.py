"""Main FastAPI entrypoint for aegis-gateway."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aegis_common.errors import AegisError
from aegis_common.logging import configure_logging, get_logger
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from aegis_gateway.api.routes_auth import router as auth_router
from aegis_gateway.api.routes_health import router as health_router
from aegis_gateway.api.routes_investigations import router as investigations_router
from aegis_gateway.api.routes_metrics import router as metrics_router
from aegis_gateway.api.routes_policies import router as policies_router
from aegis_gateway.api.routes_simulations import router as simulations_router
from aegis_gateway.api.routes_transactions import router as transactions_router
from aegis_gateway.bootstrap import build_gateway_service
from aegis_gateway.settings import GatewaySettings

logger = get_logger("aegis.gateway")


def create_app(settings: GatewaySettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application for api-gateway."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan context manager for startup and shutdown."""
        resolved = settings or GatewaySettings()
        configure_logging(log_level=resolved.aegis_log_level)
        logger.info(
            "Starting Aegis API Gateway",
            env=resolved.aegis_env,
            adapter_mode=resolved.aegis_adapter_mode,
            analyze_mode=resolved.aegis_analyze_mode,
            port=resolved.aegis_port,
        )
        app.state.settings = resolved
        app.state.service = build_gateway_service(resolved)
        yield
        logger.info("Stopping Aegis API Gateway")

    app = FastAPI(
        title="Aegis AI Fraud Ops - API Gateway",
        description="Edge transaction intake, validation, and multi-agent dispatch service",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Register error handlers for RFC 7807 problem details
    @app.exception_handler(AegisError)
    async def aegis_error_handler(request: Request, exc: AegisError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem_details(instance=str(request.url.path)),
            media_type="application/problem+json",
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "type": "urn:aegis:error:validation",
                "title": "Validation Failed",
                "status": 422,
                "detail": "Request payload failed schema validation",
                "instance": str(request.url.path),
                "details": {"errors": exc.errors()},
            },
            media_type="application/problem+json",
        )

    # Include routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(policies_router)
    app.include_router(transactions_router)
    app.include_router(investigations_router)
    app.include_router(simulations_router)
    app.include_router(metrics_router)

    return app


app = create_app()
