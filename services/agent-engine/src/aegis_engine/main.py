"""Main FastAPI entrypoint for agent-engine service."""

import base64
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from aegis_common.errors import AegisError
from aegis_common.logging import configure_logging, get_logger
from aegis_common.schemas.transaction import Transaction
from aegis_common.schemas.verdict import Verdict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from aegis_engine.bootstrap import EngineContainer, build_engine
from aegis_engine.settings import EngineSettings

logger = get_logger("aegis.engine")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str


def create_app(settings: EngineSettings | None = None) -> FastAPI:
    """Create and configure the FastAPI application for agent-engine."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Application lifespan setup."""
        resolved_settings = settings or EngineSettings()
        configure_logging(log_level=resolved_settings.aegis_log_level)
        logger.info(
            "Starting Aegis Agent Engine",
            env=resolved_settings.aegis_env,
            adapter_mode=resolved_settings.aegis_adapter_mode,
            orchestrator_model=resolved_settings.aegis_model_orchestrator,
            specialist_model=resolved_settings.aegis_model_specialist,
        )
        container = build_engine(resolved_settings)
        app.state.engine = container
        app.state.settings = resolved_settings
        yield
        logger.info("Stopping Aegis Agent Engine")

    app = FastAPI(
        title="Aegis AI Fraud Ops - Agent Engine",
        description="Google ADK multi-agent pipeline and Gemini investigation engine",
        version="1.0.0",
        lifespan=lifespan,
    )

    # RFC 7807 Problem Details handler
    @app.exception_handler(AegisError)
    async def aegis_error_handler(request: Request, exc: AegisError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_problem_details(instance=str(request.url.path)),
            headers={"Content-Type": "application/problem+json"},
        )

    @app.get("/health", response_model=HealthResponse)
    @app.get("/healthz", response_model=HealthResponse)
    async def healthz() -> HealthResponse:
        """Liveness probe."""
        return HealthResponse(status="ok", service="aegis-engine")

    @app.get("/readyz", response_model=HealthResponse)
    async def readyz() -> HealthResponse:
        """Readiness probe."""
        return HealthResponse(status="ready", service="aegis-engine")

    @app.post("/internal/investigate", response_model=Verdict)
    async def investigate_transaction(tx: Transaction, request: Request) -> Verdict:
        """Synchronously execute the ADK multi-agent investigation pipeline."""
        container: EngineContainer = request.app.state.engine
        logger.info("Internal investigate request received", tx_id=tx.tx_id, user_id=tx.user_id)
        verdict = await container.service.investigate(tx)
        return verdict

    @app.post("/internal/pubsub/tx-ingested")
    async def pubsub_push_handler(payload: dict[str, Any], request: Request) -> dict[str, str]:
        """Handle Pub/Sub push messages containing transactions to investigate."""
        container: EngineContainer = request.app.state.engine

        try:
            # Check for standard GCP Pub/Sub push envelope
            if "message" in payload and "data" in payload["message"]:
                raw_bytes = base64.b64decode(payload["message"]["data"])
                tx_data = json.loads(raw_bytes.decode("utf-8"))
            else:
                tx_data = payload

            tx = Transaction.model_validate(tx_data)
            logger.info("PubSub push message decoded", tx_id=tx.tx_id)
            await container.service.investigate(tx)
            return {"status": "acknowledged", "tx_id": tx.tx_id}
        except Exception as exc:
            logger.error("PubSub push processing failed", error=str(exc))
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid push envelope or transaction data: {exc}",
            ) from exc

    return app


app = create_app()
