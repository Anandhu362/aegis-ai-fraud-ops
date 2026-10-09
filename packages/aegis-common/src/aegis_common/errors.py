"""Aegis exception taxonomy with RFC 7807 Problem Details mapping."""

from typing import Any


class AegisError(Exception):
    """Base exception for all domain and service errors in Aegis."""

    status_code: int = 500
    error_type: str = "urn:aegis:error:internal"
    title: str = "Internal System Error"

    def __init__(
        self,
        message: str,
        *,
        detail: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or message
        self.details = details or {}

    def to_problem_details(self, instance: str | None = None) -> dict[str, Any]:
        """Convert error to RFC 7807 Problem Details format."""
        problem: dict[str, Any] = {
            "type": self.error_type,
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }
        if instance:
            problem["instance"] = instance
        if self.details:
            problem["details"] = self.details
        return problem


class ValidationError(AegisError):
    """Raised when incoming transaction or payload validation fails."""

    status_code: int = 400
    error_type: str = "urn:aegis:error:validation"
    title: str = "Validation Failed"


class AuthenticationError(AegisError):
    """Raised when authentication credentials are missing or invalid."""

    status_code: int = 401
    error_type: str = "urn:aegis:error:unauthorized"
    title: str = "Unauthorized"


class PermissionDeniedError(AegisError):
    """Raised when caller lacks required role or scope."""

    status_code: int = 403
    error_type: str = "urn:aegis:error:forbidden"
    title: str = "Forbidden"


class NotFoundError(AegisError):
    """Raised when requested transaction, case, or account is not found."""

    status_code: int = 404
    error_type: str = "urn:aegis:error:not-found"
    title: str = "Resource Not Found"


class RateLimitExceededError(AegisError):
    """Raised when request rate limit is exceeded."""

    status_code: int = 429
    error_type: str = "urn:aegis:error:rate-limit"
    title: str = "Too Many Requests"


class ModelInferenceError(AegisError):
    """Raised when Gemini or external model call times out or returns unparsable output."""

    status_code: int = 502
    error_type: str = "urn:aegis:error:model-inference"
    title: str = "Model Inference Error"


class ActuatorError(AegisError):
    """Raised when consequential core-banking or notification actuation fails."""

    status_code: int = 502
    error_type: str = "urn:aegis:error:actuator-failed"
    title: str = "Actuator Execution Failed"
