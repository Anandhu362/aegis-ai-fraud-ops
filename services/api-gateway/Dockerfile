# ==============================================================================
# Aegis AI Fraud Ops - API Gateway Microservice Dockerfile
# Multi-stage, lean, secure Python 3.12 container
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build virtual environment with uv
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation and frozen sync
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy workspace configurations and lockfiles
COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY services/api-gateway/ services/api-gateway/

# Install gateway dependencies into isolated virtualenv
RUN uv sync --no-dev --package aegis-gateway

# ------------------------------------------------------------------------------
# Stage 2: Minimal runtime image
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

# Create non-privileged service user for banking compliance
RUN groupadd -r aegis && useradd -r -g aegis -s /bin/false aegis

WORKDIR /app

# Copy virtualenv and application from builder
COPY --from=builder --chown=aegis:aegis /app/.venv /app/.venv
COPY --from=builder --chown=aegis:aegis /app/packages /app/packages
COPY --from=builder --chown=aegis:aegis /app/services/api-gateway /app/services/api-gateway
COPY --chown=aegis:aegis config/ /app/config/

# Set environment paths
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

USER aegis

EXPOSE 8080

# Cloud Run injects $PORT dynamically; default to 8080
CMD exec uvicorn aegis_gateway.main:app --host 0.0.0.0 --port ${PORT:-8080} --no-access-log
