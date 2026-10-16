"""Request dependencies: caller identity and service access."""

from aegis_common.errors import AuthenticationError
from fastapi import Request

from aegis_actuator.application.actions import ActuatorService
from aegis_actuator.settings import ActuatorSettings


def get_service(request: Request) -> ActuatorService:
    """Return the ActuatorService built during application startup."""
    service: ActuatorService = request.app.state.service
    return service


def require_caller(request: Request) -> str:
    """Resolve the authenticated caller identity.

    Fails closed: OIDC service-to-service token verification (spec 06 §4) is not
    implemented yet, so requests are only accepted in offline mock mode.

    Raises:
        AuthenticationError: When not running in mock mode.
    """
    settings: ActuatorSettings = request.app.state.settings
    if settings.is_mock_mode:
        return "mock-caller"
    raise AuthenticationError(
        "Caller authentication unavailable",
        detail="OIDC verification is not implemented; actuator refuses requests outside mock mode",
    )
