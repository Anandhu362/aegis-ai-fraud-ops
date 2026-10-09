"""Authentication and identity token validation helpers."""

from typing import Any

from aegis_common.errors import AuthenticationError


def verify_api_key(provided_key: str | None, expected_keys: set[str]) -> bool:
    """Validate an incoming API key against configured valid keys."""
    if not provided_key or not expected_keys:
        return False
    return provided_key in expected_keys


def mock_verify_oidc_token(token: str | None) -> dict[str, Any]:
    """Mock verification for local offline development."""
    if not token or token.lower() in ("invalid", "expired"):
        raise AuthenticationError("Invalid or expired authentication token")
    return {
        "sub": "user_mock_001",
        "email": "analyst@aegis.dev",
        "role": "analyst",
    }
