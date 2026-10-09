# 06 · Backend Specification

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Related | [02_ARCHITECTURE](./02_ARCHITECTURE.md) · [04_AGENTS_SPEC](./04_AGENTS_SPEC.md) · [08_DATA_SCHEMAS_API](./08_DATA_SCHEMAS_API.md) |

---

## 1. Technology Stack

| Concern | Choice | Version policy |
|---------|--------|----------------|
| Language | Python | **3.12** |
| Package / env manager | **uv** (workspace mode) | Locked via `uv.lock` |
| Web framework | FastAPI | ≥ 0.115 |
| ASGI server | Uvicorn (`--workers 1`, Cloud Run scales instances) | ≥ 0.30 |
| Validation / settings | Pydantic v2, `pydantic-settings` | ≥ 2.8 |
| Agents | `google-adk` | **Pinned exact** (fast-moving) |
| LLM client | `google-genai` (Vertex mode) | Pinned minor |
| Firestore | `google-cloud-firestore` (`AsyncClient`) | ≥ 2.16 |
| BigQuery | `google-cloud-bigquery` (+ `bigquery-storage` for writes) | ≥ 3.25 |
| Pub/Sub | `google-cloud-pubsub` | ≥ 2.23 |
| HTTP client | `httpx` (async, connection pooling) | ≥ 0.27 |
| Service-to-service auth | `google-auth` ID tokens | — |
| Retries | `tenacity` | — |
| Logging | `structlog` → JSON (Cloud Logging format) | — |
| Tracing | OpenTelemetry + Cloud Trace exporter | — |
| Config files | YAML (`risk_policy.yaml`) via `pyyaml` | — |
| Lint / format | Ruff | — |
| Types | mypy `--strict` | — |
| Tests | pytest, pytest-asyncio, respx, hypothesis, freezegun | — |

> v0 `requirements.txt` is replaced by per-service `pyproject.toml` + a root uv workspace. `requirements.txt` can be exported for Docker with `uv export`.

---

## 2. Layered (Hexagonal) Architecture — per service

```text
┌──────────────────────────────────────────────────────────────┐
│  api/            FastAPI routers, request/response DTOs,     │  ← HTTP edge only
│                  auth dependencies, error handlers           │
├──────────────────────────────────────────────────────────────┤
│  application/    Use cases (AnalyzeTransaction,              │  ← orchestration of domain + ports
│                  RunInvestigation, LockAccount), ADK pipeline│
├──────────────────────────────────────────────────────────────┤
│  domain/         Pure models, scoring, policy, haversine,    │  ← NO I/O, NO GCP imports
│                  structuring, enums, errors                  │
├──────────────────────────────────────────────────────────────┤
│  ports/          typing.Protocol interfaces                  │  ← contracts
├──────────────────────────────────────────────────────────────┤
│  adapters/       gcp/ (firestore, bigquery, pubsub, genai,   │  ← I/O implementations
│                  actuator_http) · mock/ (in-memory, fixtures)│
├──────────────────────────────────────────────────────────────┤
│  bootstrap.py    Composition root: builds adapters from      │  ← DI wiring
│                  Settings, injects into use cases            │
└──────────────────────────────────────────────────────────────┘
```

**Dependency rule:** `api → application → domain`; `application → ports`; `adapters → ports + domain`. Domain imports nothing from other layers. An `import-linter` contract in CI enforces this.

---

## 3. Services & Module Layout

### 3.1 `packages/aegis-common` (shared library)
```text
src/aegis_common/
├── schemas/            # Pydantic models shared across services (Transaction, Verdict, TelemetryEvent, enums)
├── logging.py          # structlog config, PII masking processor, trace correlation
├── tracing.py          # OpenTelemetry setup
├── auth.py             # OIDC token verification helpers, ID-token fetcher
├── errors.py           # AegisError hierarchy → RFC 7807 mapping
└── settings_base.py    # BaseSettings with common GCP fields
```

### 3.2 `services/api-gateway`
```text
src/aegis_gateway/
├── main.py                       # create_app(), lifespan (clients init/close)
├── bootstrap.py
├── settings.py
├── api/
│   ├── deps.py                   # auth (API key / Firebase ID token), rate limiter
│   ├── routes_transactions.py    # POST /v1/transactions:analyze, alias /api/analyze-tx
│   ├── routes_investigations.py  # GET /v1/investigations/{tx_id}, POST .../decision
│   ├── routes_simulations.py     # POST /v1/simulations/{scenario}
│   ├── routes_metrics.py         # GET /v1/metrics/summary
│   └── routes_health.py
├── application/
│   ├── analyze_transaction.py
│   ├── simulation_scenarios.py   # coffee / smurfing / tor_travel generators
│   └── analyst_decision.py
├── ports/  (dispatcher.py, investigation_repo.py, rate_limiter.py)
└── adapters/
    ├── gcp/ (pubsub_dispatcher.py, http_dispatcher.py, firestore_repo.py)
    └── mock/
```

### 3.3 `services/agent-engine`
```text
src/aegis_engine/
├── main.py                       # POST /internal/pubsub/tx-ingested, POST /internal/investigate (sync)
├── bootstrap.py
├── settings.py
├── config/risk_policy.yaml       # weights, thresholds, bands (versioned)
├── prompts/                      # behavioral.md, threat_intel.md, orchestrator.md, deep_review.md
├── domain/
│   ├── features.py               # FeatureVector + sub-models
│   ├── scoring.py                # compute_base_score(), apply_hard_rules(), apply_adjustment()
│   ├── policy.py                 # decide(), band mapping
│   ├── geo.py                    # haversine, travel speed
│   ├── velocity.py               # structuring / burst detection
│   └── reports.py                # BehavioralReport, ThreatReport, OrchestratorAssessment
├── agents/
│   ├── pipeline.py               # build_pipeline() → SequentialAgent tree
│   ├── intake.py                 # IntakeAgent(BaseAgent)
│   ├── enrichment.py             # EnrichmentAgent(BaseAgent)
│   ├── triage.py                 # TriageGate(BaseAgent)
│   ├── behavioral.py             # build_behavioral_agent() → LlmAgent
│   ├── threat_intel.py           # build_threat_intel_agent() → LlmAgent
│   ├── orchestrator.py           # build_orchestrator_agent() → LlmAgent
│   ├── policy_agent.py           # PolicyAgent(BaseAgent)
│   ├── closeout.py               # CloseoutAgent(BaseAgent)
│   └── deep_review.py            # async Pro narrative
├── tools/
│   ├── baseline.py               # get_user_baseline
│   ├── velocity.py               # get_velocity_window
│   ├── ip_reputation.py          # lookup_ip_reputation
│   ├── travel.py                 # verify_velocity_travel
│   └── device.py                 # check_device
├── application/
│   ├── run_investigation.py      # use case wrapping ADK Runner + timeouts + degraded fallback
│   └── telemetry.py              # TelemetryEmitter (seq, masking, batching)
├── ports/  (profile_store.py, baseline_source.py, ip_intel.py, actuator.py, telemetry_sink.py, results_sink.py)
└── adapters/
    ├── gcp/ (firestore_profiles.py, bigquery_baselines.py, firestore_telemetry.py,
    │         bigquery_results.py, actuator_http.py, tor_list_intel.py)
    └── mock/
```

### 3.4 `services/actuator`
```text
src/aegis_actuator/
├── main.py
├── api/routes_accounts.py        # POST /v1/accounts/{user_id}:lock | :unlock, GET /v1/accounts/{user_id}
├── api/routes_alerts.py          # POST /v1/alerts
├── application/ (lock_account.py, unlock_account.py, dispatch_alert.py)
├── ports/ (ledger.py, notifier.py, audit_log.py)
└── adapters/ (firestore_ledger.py, log_notifier.py, whatsapp_notifier.py, mock/)
```

---

## 4. API Endpoints

### api-gateway (public, via Firebase Hosting rewrite `/api/**`)
| Method | Path | Auth | Description | Responses |
|--------|------|------|-------------|-----------|
| POST | `/v1/transactions:analyze` | API key / ID token | Submit tx; `?mode=async\|sync` (default async) | 202 `{tx_id, status_url}` · 200 `Verdict` (sync) · 409 · 422 · 429 |
| POST | `/api/analyze-tx` | same | **v0 alias** → above | same |
| GET | `/v1/investigations/{tx_id}` | ID token | Snapshot of case + verdict | 200 · 404 |
| POST | `/v1/investigations/{tx_id}/decision` | ID token (role `analyst`) | Analyst override: `{action: APPROVE\|CONFIRM_FRAUD\|UNLOCK, reason}` | 200 · 403 |
| POST | `/v1/simulations/{scenario}` | ID token / API key | `coffee`, `smurfing`, `tor_travel`; returns list of tx_ids | 202 |
| GET | `/v1/metrics/summary` | ID token | KPIs (processed, blocked, $ protected, latency, last eval) | 200 |
| GET | `/healthz`, `/readyz` | none | Liveness / readiness | 200 · 503 |

### agent-engine (internal)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/internal/pubsub/tx-ingested` | Pub/Sub OIDC | Push endpoint; returns 2xx to ack, 5xx to retry |
| POST | `/internal/investigate` | OIDC (`sa-gateway`) | Sync investigation; returns `Verdict` |

### actuator (internal)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/v1/accounts/{user_id}:lock` | OIDC (`sa-agent-engine`) | `Idempotency-Key` header required |
| POST | `/v1/accounts/{user_id}:unlock` | OIDC (`sa-gateway`) | Analyst unlock; reason required |
| POST | `/v1/transactions/{tx_id}:block` | OIDC | Decline transaction |
| POST | `/v1/alerts` | OIDC | Dispatch customer alert |

**Error format:** RFC 7807 `application/problem+json`:
```json
{ "type": "https://aegis.dev/errors/duplicate-transaction", "title": "Duplicate transaction",
  "status": 409, "detail": "tx_id TX_982341 already submitted", "instance": "/v1/transactions:analyze",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736" }
```

---

## 5. Configuration (`pydantic-settings`)

| Env var | Service | Default | Description |
|---------|---------|---------|-------------|
| `GCP_PROJECT` | all | — | Project ID |
| `AEGIS_ENV` | all | `local` | `local` · `dev` · `demo` |
| `AEGIS_ADAPTER_MODE` | all | `mock` (local) / `gcp` | Selects adapters |
| `AEGIS_LOG_LEVEL` | all | `INFO` | |
| `AEGIS_ANALYZE_MODE` | gateway | `async` | `async` (Pub/Sub) or `sync` (HTTP) |
| `AEGIS_PUBSUB_TOPIC` | gateway | `tx-ingest` | |
| `AEGIS_ENGINE_URL` | gateway | — | Sync-mode target |
| `AEGIS_API_KEYS_SECRET` | gateway | `aegis-api-keys` | Secret Manager name |
| `AEGIS_RATE_LIMIT_RPS` | gateway | `20` | |
| `AEGIS_MODEL_ORCHESTRATOR` / `_FALLBACK` | engine | see [03](./03_AI_MODEL_STRATEGY.md) | |
| `AEGIS_MODEL_SPECIALIST` / `_FALLBACK` | engine | see 03 | |
| `AEGIS_MODEL_DEEP_REVIEW` | engine | see 03 | |
| `AEGIS_VERTEX_LOCATION` | engine | `global` | |
| `AEGIS_ACTUATOR_URL` | engine, gateway | — | |
| `AEGIS_RISK_POLICY_PATH` | engine | `config/risk_policy.yaml` | |
| `AEGIS_TIMEOUT_PIPELINE_MS` | engine | `6000` | Global cap |
| `AEGIS_TIMEOUT_LLM_MS` | engine | `1500` | Per LLM call |
| `AEGIS_BQ_DATASET` | engine, jobs | `fraud_telemetry` | |
| `AEGIS_NOTIFIER` | actuator | `log` | `log` · `whatsapp` |
| `FIRESTORE_EMULATOR_HOST` | local | — | Auto-used by SDK when set |

---

## 6. Reference Code Skeletons

> These skeletons fix the **shape** of the code. Check ADK/GenAI APIs against the pinned versions when implementing.

### 6.1 Settings
```python
# services/agent-engine/src/aegis_engine/settings.py
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EngineSettings(BaseSettings):
    """Runtime configuration for the agent engine, loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", extra="ignore")

    gcp_project: str = Field(alias="GCP_PROJECT")
    env: Literal["local", "dev", "demo"] = "local"
    adapter_mode: Literal["mock", "gcp"] = "mock"
    vertex_location: str = "global"
    model_orchestrator: str
    model_orchestrator_fallback: str
    model_specialist: str
    model_specialist_fallback: str
    model_deep_review: str
    actuator_url: str = ""
    risk_policy_path: str = "config/risk_policy.yaml"
    timeout_pipeline_ms: int = 6000
    timeout_llm_ms: int = 1500
    bq_dataset: str = "fraud_telemetry"


@lru_cache
def get_settings() -> EngineSettings:
    return EngineSettings()  # type: ignore[call-arg]
```

### 6.2 Domain scoring (pure, 95 %+ test coverage)
```python
# services/agent-engine/src/aegis_engine/domain/scoring.py
from dataclasses import dataclass

from aegis_engine.domain.features import FeatureVector
from aegis_engine.domain.policy import RiskPolicy


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    base: int
    after_rules: int
    floor: int
    fired_signals: dict[str, int]  # e.g. {"S1_monetary": 25, "S6_tor": 30}
    fired_rules: tuple[str, ...]  # e.g. ("H1",)


def compute_deterministic_score(f: FeatureVector, p: RiskPolicy) -> ScoreBreakdown:
    """Compute the base score and hard-rule floor from verified features only."""
    signals: dict[str, int] = {}
    z = f.monetary.z_score
    if z >= 4:
        signals["S1_monetary"] = p.w.monetary_extreme
    elif z >= 3:
        signals["S1_monetary"] = p.w.monetary_high
    elif z >= 2:
        signals["S1_monetary"] = p.w.monetary_moderate
    if f.category.is_novel:
        signals["S2_category_novelty"] = p.w.category_novelty
    if f.category.is_high_risk:
        signals["S3_high_risk_category"] = p.w.high_risk_category
    if f.velocity.structuring_hit:
        signals["S4_structuring"] = p.w.structuring_hit
    elif f.velocity.in_structuring_band:
        signals["S4_structuring"] = p.w.structuring_band
    if f.velocity.count_60s >= p.velocity_burst_count:
        signals["S5_velocity_burst"] = p.w.velocity_burst
    if f.ip.is_tor:
        signals["S6_anon_network"] = p.w.tor
    elif f.ip.is_vpn or f.ip.is_hosting:
        signals["S6_anon_network"] = p.w.vpn
    # ... S7–S10 analogous

    base = min(100, sum(signals.values()))
    floor, rules = 0, []
    if f.ip.is_tor and f.travel.impossible:
        floor, rules = max(floor, p.h1_floor), [*rules, "H1"]
    if f.velocity.structuring_hit:
        floor, rules = max(floor, p.h2_floor), [*rules, "H2"]
    return ScoreBreakdown(base, max(base, floor), floor, signals, tuple(rules))


def apply_llm_adjustment(b: ScoreBreakdown, adjustment: int) -> int:
    """Apply the bounded orchestrator adjustment without breaching hard-rule floors."""
    bounded = max(-10, min(10, adjustment))
    return max(b.floor, min(100, max(0, b.after_rules + bounded)))
```

### 6.3 Custom ADK agent (Enrichment)
```python
# services/agent-engine/src/aegis_engine/agents/enrichment.py
import asyncio
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from pydantic import ConfigDict

from aegis_engine.application.telemetry import TelemetryEmitter
from aegis_engine.tools.toolbox import Toolbox


class EnrichmentAgent(BaseAgent):
    """Runs all deterministic tools concurrently and writes `features` to session state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    toolbox: Toolbox
    telemetry: TelemetryEmitter

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        tx = ctx.session.state["tx"]
        await self.telemetry.tool_call(
            "Behavioral Analyst", f"Fetching 90-day baseline for {tx['user_id']}."
        )
        await self.telemetry.tool_call(
            "Threat Intel", f"Checking IP {tx['ip_address']} reputation."
        )
        baseline, velocity, ip_rep, travel, device = await asyncio.gather(
            self.toolbox.baseline(tx["user_id"]),
            self.toolbox.velocity(tx["user_id"], tx["timestamp"]),
            self.toolbox.ip_reputation(tx["ip_address"]),
            self.toolbox.travel(tx["user_id"], tx["location"], tx["timestamp"]),
            self.toolbox.device(tx["user_id"], tx["device_id"]),
            return_exceptions=True,  # one failing tool never fails the pipeline
        )
        features = self.toolbox.assemble(tx, baseline, velocity, ip_rep, travel, device)
        await self.telemetry.tool_results(features)
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"features": features.model_dump(mode="json")}),
        )
```

### 6.4 Specialist LlmAgent factory
```python
# services/agent-engine/src/aegis_engine/agents/behavioral.py
from google.adk.agents import LlmAgent
from google.genai import types

from aegis_engine.domain.reports import BehavioralReport
from aegis_engine.prompts import PromptRegistry


def build_behavioral_agent(model: str, prompts: PromptRegistry) -> LlmAgent:
    prompt = prompts.get("behavioral")
    return LlmAgent(
        name="BehavioralAnalyst",
        model=model,
        description="Interprets behavioral and monetary features for fraud signals.",
        instruction=prompt.text,  # references {features} / {tx} from session state
        output_schema=BehavioralReport,
        output_key="behavioral_report",
        generate_content_config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=384),
    )
```

### 6.5 Pipeline assembly
```python
# services/agent-engine/src/aegis_engine/agents/pipeline.py
from google.adk.agents import ParallelAgent, SequentialAgent


def build_pipeline(deps: "EngineDeps") -> SequentialAgent:
    return SequentialAgent(
        name="InvestigationPipeline",
        sub_agents=[
            IntakeAgent(name="Intake", telemetry=deps.telemetry),
            EnrichmentAgent(name="Enrichment", toolbox=deps.toolbox, telemetry=deps.telemetry),
            TriageGate(name="Triage", policy=deps.policy, telemetry=deps.telemetry),
            ParallelAgent(
                name="SpecialistPanel",
                sub_agents=[
                    build_behavioral_agent(deps.settings.model_specialist, deps.prompts),
                    build_threat_intel_agent(deps.settings.model_specialist, deps.prompts),
                ],
            ),
            build_orchestrator_agent(deps.settings.model_orchestrator, deps.prompts),
            PolicyAgent(
                name="Policy", policy=deps.policy, actuator=deps.actuator, telemetry=deps.telemetry
            ),
            CloseoutAgent(name="Closeout", results=deps.results_sink, telemetry=deps.telemetry),
        ],
    )
```

### 6.6 Telemetry emitter (ordered, masked)
```python
# services/agent-engine/src/aegis_engine/application/telemetry.py
import asyncio
import time

from aegis_common.logging import mask_pii
from aegis_common.schemas import TelemetryEvent
from aegis_engine.ports.telemetry_sink import TelemetrySink


class TelemetryEmitter:
    """Assigns monotonic sequence numbers and forwards PII-masked events to the sink."""

    def __init__(self, tx_id: str, sink: TelemetrySink) -> None:
        self._tx_id, self._sink = tx_id, sink
        self._seq = 0
        self._lock = asyncio.Lock()

    async def emit(self, agent: str, action: str, message: str, **data: object) -> None:
        async with self._lock:
            self._seq += 1
            event = TelemetryEvent(
                seq=self._seq,
                agent=agent,
                action=action,
                message=mask_pii(message)[:240],
                data=data,
                timestamp=int(time.time() * 1000),
            )
        await self._sink.write(self._tx_id, event)
```

---

## 7. Concurrency, Timeouts & Resilience Rules

1. All I/O is `async`. Sync SDK calls (BigQuery) are wrapped with `asyncio.to_thread`.
2. Each stage is wrapped in `asyncio.timeout(settings.timeout_*_ms / 1000)`.
3. GCP clients are created once in the FastAPI `lifespan` and closed on shutdown. **Never at import time.**
4. Retries (tenacity): LLM 1 retry → fallback model; Firestore 3 retries; actuator 2 retries plus an idempotency key.
5. Pub/Sub push handler: return 2xx **only** after the verdict is persisted; 4xx for poison messages (to DLQ via max-delivery); 5xx for transient errors.
6. User profile updates run in a Firestore transaction **after** the verdict, so the current tx never contaminates its own baseline.

---

## 8. Logging & Observability

- `structlog` JSON with Cloud Logging fields: `severity`, `message`, `logging.googleapis.com/trace`, `tx_id`, `case_id`, `stage`, `latency_ms`.
- The PII processor masks emails, phone numbers, card-like numbers, and the last octet of IPv4 addresses.
- OpenTelemetry spans: `gateway.analyze`, `engine.pipeline`, `engine.stage.<name>`, `llm.<agent>`, `tool.<name>`, `actuator.<action>`.
- Log-based metrics: `aegis/investigations_total{decision}`, `aegis/pipeline_latency_ms`, `aegis/llm_fallback_total`, `aegis/degraded_total`.

---

## 9. Container Image (per service)

```dockerfile
# services/agent-engine/Dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY packages/aegis-common ./packages/aegis-common
COPY services/agent-engine ./services/agent-engine
RUN uv sync --frozen --no-dev --package aegis-engine

FROM python:3.12-slim AS runtime
RUN useradd --create-home --uid 10001 aegis
WORKDIR /app
COPY --from=builder --chown=aegis:aegis /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8080
USER aegis
EXPOSE 8080
CMD ["sh", "-c", "uvicorn aegis_engine.main:app --host 0.0.0.0 --port ${PORT} --no-access-log"]
```

The build context is the **repo root** (for the shared package): `docker build -f services/agent-engine/Dockerfile .`
