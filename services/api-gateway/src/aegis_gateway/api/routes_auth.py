"""Authentication endpoints for SOC Analyst session management and RBAC."""

# ruff: noqa: S105, S106, I001

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import threading
import time

from aegis_common.errors import AuthenticationError
from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# In-memory rate limiter tracking failed login attempts: {ip: [timestamps]}
_login_attempts: dict[str, list[datetime]] = {}
_attempts_lock = threading.Lock()
MAX_LOGIN_ATTEMPTS_PER_MINUTE = 5
JWT_PARTS_COUNT = 3

# Revoked tokens blacklist for logout termination: {token: revoked_timestamp}
_revoked_tokens: dict[str, float] = {}
_revocation_lock = threading.Lock()

JWT_SECRET_KEY = "aegis-production-grade-hmac-sha256-key-9f8a7c2b1e4d"


class JwtManager:
    """Deterministic, RFC 7519-compliant HMAC-SHA256 (HS256) JWT processor."""

    def __init__(self, secret: str = JWT_SECRET_KEY) -> None:
        self.secret = secret.encode()

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode().rstrip("=")

    @staticmethod
    def _b64url_decode(s: str) -> bytes:
        padding = "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s + padding)

    def encode(self, payload: dict, expires_in_seconds: int = 86400) -> str:
        """Sign and encode claims dictionary into a JWT bearer token."""
        now = int(time.time())
        claims = dict(payload)
        claims["iat"] = now
        claims["exp"] = now + expires_in_seconds
        claims["iss"] = "aegis-auth-authority"

        header = {"alg": "HS256", "typ": "JWT"}
        h_b64 = self._b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        p_b64 = self._b64url_encode(json.dumps(claims, separators=(",", ":")).encode())

        message = f"{h_b64}.{p_b64}".encode()
        sig = hmac.new(self.secret, message, hashlib.sha256).digest()
        sig_b64 = self._b64url_encode(sig)
        return f"{h_b64}.{p_b64}.{sig_b64}"

    def decode(self, token: str) -> dict:
        """Validate signature, expiration, and return decoded token payload."""
        with _revocation_lock:
            if token in _revoked_tokens:
                raise ValueError("Session token has been revoked")

        parts = token.strip().split(".")
        if len(parts) != JWT_PARTS_COUNT:
            raise ValueError("Malformed JWT bearer token")

        h_b64, p_b64, sig_b64 = parts
        message = f"{h_b64}.{p_b64}".encode()
        expected_sig = hmac.new(self.secret, message, hashlib.sha256).digest()

        try:
            actual_sig = self._b64url_decode(sig_b64)
        except Exception as err:
            raise ValueError("Invalid signature encoding") from err

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise ValueError("Invalid JWT token signature")

        try:
            payload = json.loads(self._b64url_decode(p_b64).decode("utf-8"))
        except Exception as err:
            raise ValueError("Malformed token claims payload") from err

        if int(time.time()) > payload.get("exp", 0):
            raise ValueError("Session token has expired")

        return payload


jwt_service = JwtManager()


class LoginRequest(BaseModel):
    """Analyst login credentials."""

    email: str = Field(..., description="Analyst email address")
    password: str = Field(..., description="Analyst access password")
    role: str = Field(default="L2 Senior Fraud Ops", description="Requested SOC analyst role")


class AnalystProfile(BaseModel):
    """Authenticated analyst session profile."""

    analyst_id: str
    name: str
    email: str
    role: str
    permissions: list[str]


class LoginResponse(BaseModel):
    """Authentication token and profile."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    analyst: AnalystProfile


def _check_rate_limit(client_ip: str) -> None:
    """Enforce max 5 login attempts per minute per client IP."""
    now = datetime.now(UTC)
    cutoff = now - timedelta(seconds=60)
    with _attempts_lock:
        history = [t for t in _login_attempts.get(client_ip, []) if t >= cutoff]
        if len(history) >= MAX_LOGIN_ATTEMPTS_PER_MINUTE:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please wait 60 seconds before retrying.",
            )
        history.append(now)
        _login_attempts[client_ip] = history


def get_authenticated_analyst(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> AnalystProfile:
    """FastAPI dependency to extract and verify the JWT bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError(
            "Authentication required",
            detail="Missing or malformed Authorization header. Expected 'Bearer <token>'.",
        )

    token = authorization.split("Bearer ", 1)[1].strip()
    try:
        payload = jwt_service.decode(token)
    except ValueError as err:
        raise AuthenticationError(
            "Invalid session",
            detail=str(err),
        ) from err

    return AnalystProfile(
        analyst_id=payload.get("sub", "ANALYST_01"),
        name=payload.get("name", "Analyst"),
        email=payload.get("email", "analyst@aegis.com"),
        role=payload.get("role", "L2 Senior Fraud Ops"),
        permissions=payload.get("permissions", ["triage", "investigate"]),
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate SOC Fraud Analyst",
)
async def login(req: LoginRequest, request: Request) -> LoginResponse:
    """Validate credentials on server, issue cryptographically signed JWT token."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    email_clean = req.email.strip().lower()
    # Server-side credential verification (credentials never validated client-side)
    valid_accounts = {
        "demo@aegis.com": "password",
        "demo@ageis.com": "password",
        "analyst@aegis.com": "password",
        "compliance@aegis.com": "password",
    }

    if email_clean not in valid_accounts or req.password.strip() != valid_accounts[email_clean]:
        _check_rate_limit(client_ip)
        raise AuthenticationError(
            "Invalid credentials",
            detail="Invalid email or password. Valid demo credentials: demo@aegis.com / password",
        )

    # Derive display name from email
    display_name = email_clean.split("@")[0]
    if display_name in ("demo", "ageis"):
        display_name = "Anandhu"

    # Resolve approved permissions by role
    role = req.role if req.role in (
        "L2 Senior Fraud Ops",
        "SOC Analyst",
        "Compliance Auditor",
    ) else "L2 Senior Fraud Ops"

    permissions = ["triage", "investigate"]
    if role in ("L2 Senior Fraud Ops", "SOC Analyst"):
        permissions.extend(["override", "export_bi"])
    if role == "L2 Senior Fraud Ops":
        permissions.append("actuate")

    analyst_id = f"ANL_{display_name.upper()}_01"
    analyst = AnalystProfile(
        analyst_id=analyst_id,
        name=display_name,
        email=email_clean,
        role=role,
        permissions=permissions,
    )

    # Issue cryptographically signed HMAC-SHA256 JWT
    token_claims = {
        "sub": analyst.analyst_id,
        "name": analyst.name,
        "email": analyst.email,
        "role": analyst.role,
        "permissions": analyst.permissions,
    }
    jwt_token = jwt_service.encode(token_claims, expires_in_seconds=86400)

    return LoginResponse(
        access_token=jwt_token,
        token_type="bearer",
        expires_in=86400,
        analyst=analyst,
    )


@router.get(
    "/me",
    response_model=AnalystProfile,
    summary="Verify current session and return analyst profile",
)
async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> AnalystProfile:
    """Verify incoming JWT token and return active session analyst profile."""
    return get_authenticated_analyst(authorization)


@router.post(
    "/logout",
    summary="Terminate SOC analyst session",
)
async def logout(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, str]:
    """Gracefully end active session and revoke the current JWT token."""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        with _revocation_lock:
            _revoked_tokens[token] = time.time()

    return {"status": "ok", "message": "Logged out successfully and session terminated"}
