"""Dependencies for API Gateway routes."""

from aegis_common.errors import AuthenticationError
from fastapi import Header, Request

from aegis_gateway.application.gateway_service import GatewayService
from aegis_gateway.settings import GatewaySettings


def get_gateway_service(request: Request) -> GatewayService:
    """Retrieve GatewayService from application state."""
    service: GatewayService = request.app.state.service
    return service


def verify_auth_or_mock(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify caller authentication (API key or mock dev bypass).

    In mock mode (AEGIS_ADAPTER_MODE=mock) or local environment, allows requests
    without key or with demo key for seamless local testing.
    """
    settings: GatewaySettings = request.app.state.settings

    if settings.is_mock_mode or settings.aegis_env in ("local", "dev"):
        return "mock-authenticated-analyst"

    if x_api_key and x_api_key == "aegis-secret-key":
        return "api-key-caller"

    raise AuthenticationError(
        "Missing or invalid API key",
        detail="Header 'X-API-Key' is required for production gateway endpoints",
    )
