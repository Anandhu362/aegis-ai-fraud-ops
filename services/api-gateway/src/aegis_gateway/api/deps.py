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
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    """Verify caller authentication (JWT Bearer token, API key, or demo bypass)."""
    # 1. Verify JWT Bearer token from authenticated analyst session
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        try:
            from aegis_gateway.api.routes_auth import jwt_service  # noqa: PLC0415

            payload = jwt_service.decode(token)
            return str(payload.get("sub", "authenticated-analyst"))
        except (ValueError, KeyError):
            # Token invalid or expired; continue to API key or demo environment evaluation
            pass

    # 2. Verify API key from authorized switches or clients
    if x_api_key and x_api_key in ("aegis-secret-key", "demo-key", "key-fw-9812", "key-vs-1042"):
        return "api-key-caller"

    # 3. Environment bypass for local, dev, and demo
    settings: GatewaySettings = request.app.state.settings
    if settings.is_mock_mode or settings.aegis_env.lower() in ("local", "dev", "demo"):
        return "mock-authenticated-analyst"

    raise AuthenticationError(
        "Missing or invalid authentication",
        detail="A valid Bearer JWT session token or 'X-API-Key' is required",
    )
