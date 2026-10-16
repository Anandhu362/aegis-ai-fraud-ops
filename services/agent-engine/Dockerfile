# ==============================================================================
# Aegis AI Fraud Ops - Agent Engine Microservice Dockerfile
# Multi-stage, lean, secure Python 3.12 container for Google ADK Pipeline
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build virtual environment with uv
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:0.6-python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY packages/ packages/
COPY services/agent-engine/ services/agent-engine/

# Install engine dependencies into isolated virtualenv
RUN uv sync --frozen --no-dev --package aegis-engine

# ------------------------------------------------------------------------------
# Stage 2: Minimal runtime image
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner

RUN groupadd -r aegis && useradd -r -g aegis -s /bin/false aegis

WORKDIR /app

COPY --from=builder --chown=aegis:aegis /app/.venv /app/.venv
COPY --from=builder --chown=aegis:aegis /app/packages /app/packages
COPY --from=builder --chown=aegis:aegis /app/services/agent-engine /app/services/agent-engine
COPY --chown=aegis:aegis config/ /app/config/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8090

USER aegis

EXPOSE 8090

CMD exec uvicorn aegis_engine.main:app --host 0.0.0.0 --port ${PORT:-8090} --no-access-log
