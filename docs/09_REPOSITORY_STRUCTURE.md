# 09 · Repository Structure

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Repo type | Monorepo (Python **uv workspace** + npm frontend) |

---

## 1. Full Tree

```text
aegis-ai-fraud-ops/
├── README.md                          # Overview + doc index
├── PROJECT_SPEC.md                    # Original v0 spec (reference only)
├── AGENTS.md                          # Rules for AI coding assistants
├── LICENSE
├── .gitignore · .gitattributes · .editorconfig
├── .env.example                       # All env vars, documented (no secrets)
├── .pre-commit-config.yaml            # ruff, mypy, prettier, eslint, gitleaks, end-of-file
├── Taskfile.yml                       # Cross-platform task runner (Windows/macOS/Linux)
├── pyproject.toml                     # uv workspace root + shared ruff/mypy/pytest config
├── uv.lock
│
├── docs/
│   ├── 01_PROJECT_ANALYSIS.md … 14_ROADMAP_TASKS.md
│   ├── adr/                           # 001-google-adk.md, 002-deterministic-scoring.md, …
│   ├── diagrams/                      # exported PNG/SVG for pitch deck
│   └── runbooks/                      # demo-day.md, incident-llm-outage.md, rotate-api-key.md
│
├── contracts/
│   └── jsonschema/                    # Generated from Pydantic (transaction, verdict, telemetry_event, …)
│
├── packages/
│   └── aegis-common/                  # Shared Python library
│       ├── pyproject.toml
│       ├── src/aegis_common/ (schemas/, logging.py, tracing.py, auth.py, errors.py, settings_base.py)
│       └── tests/
│
├── services/
│   ├── api-gateway/
│   │   ├── pyproject.toml · Dockerfile · .dockerignore
│   │   ├── src/aegis_gateway/ (main.py, bootstrap.py, settings.py, api/, application/, ports/, adapters/)
│   │   └── tests/ (unit/, integration/, contract/)
│   ├── agent-engine/
│   │   ├── pyproject.toml · Dockerfile · .dockerignore
│   │   ├── src/aegis_engine/
│   │   │   ├── main.py · bootstrap.py · settings.py
│   │   │   ├── config/risk_policy.yaml
│   │   │   ├── prompts/ (behavioral.md, threat_intel.md, orchestrator.md, deep_review.md)
│   │   │   ├── domain/ · agents/ · tools/ · application/ · ports/ · adapters/
│   │   └── tests/ (unit/, integration/, golden/, evals/)
│   └── actuator/
│       ├── pyproject.toml · Dockerfile · .dockerignore
│       ├── src/aegis_actuator/ (main.py, api/, application/, ports/, adapters/)
│       └── tests/
│
├── jobs/
│   ├── baseline-sync/                 # BigQuery user_baselines → Firestore user_profiles
│   └── intel-refresh/                 # Tor exit list / ASN lists refresh
│
├── simulation/
│   ├── pyproject.toml
│   ├── bq_schema.json                 # historical_txs schema (explicit)
│   ├── src/aegis_sim/
│   │   ├── generate_sims.py           # 500 users × 10,000 txs (seeded)
│   │   ├── scenarios.py               # coffee / smurfing / tor_travel / hard negatives
│   │   ├── build_eval_set.py          # 1,500 benign + 500 adversarial
│   │   ├── run_adversarial_test.py    # concurrent runner + metrics
│   │   └── report.py                  # Markdown/JSON report + BigQuery eval_runs
│   ├── data/                          # .gitignored outputs (CSV, eval sets)
│   └── tests/
│
├── frontend/                          # (see 07_FRONTEND_SPEC.md §4)
│   ├── src/ · public/ · tests/
│   ├── firebase.json · .firebaserc · firestore.rules · firestore.indexes.json
│   └── package.json · vite.config.ts · tsconfig.json · eslint.config.js
│
├── infra/
│   ├── terraform/                     # Optional IaC (preferred for "enterprise" story)
│   │   ├── modules/ (cloud_run_service, pubsub, firestore, bigquery, iam, scheduler)
│   │   └── envs/ (dev/, demo/)
│   └── scripts/                       # gcloud fallback scripts (bootstrap.ps1 / bootstrap.sh)
│
├── scripts/
│   ├── check_models.py                # Verify Gemini model IDs (see 03 §3.1)
│   ├── export_schemas.py              # Pydantic → contracts/jsonschema
│   └── seed_local.py                  # Seed Firestore emulator with profiles + intel
│
└── .github/
    ├── workflows/ (ci.yml, deploy.yml, nightly-eval.yml)
    ├── PULL_REQUEST_TEMPLATE.md
    ├── ISSUE_TEMPLATE/ (bug.yml, feature.yml)
    └── CODEOWNERS
```

---

## 2. Mapping from v0 Layout

| v0 path | v1 path | Change reason |
|---------|---------|---------------|
| `backend/main.py` | `services/api-gateway/src/aegis_gateway/main.py` + `services/agent-engine/src/aegis_engine/main.py` | Split edge vs. engine |
| `backend/config.py` | `services/*/settings.py` + `packages/aegis-common/settings_base.py` | Typed settings per service |
| `backend/agents/orchestrator.py` | `services/agent-engine/src/aegis_engine/agents/orchestrator.py` + `pipeline.py` | ADK tree |
| `backend/agents/behavioral.py` | `.../agents/behavioral.py` | LlmAgent factory |
| `backend/agents/threat_intel.py` | `.../agents/threat_intel.py` | LlmAgent factory |
| `backend/tools/bq_client.py` | `.../tools/baseline.py` + `.../adapters/gcp/bigquery_baselines.py` | Port/adapter split |
| `backend/tools/osint_client.py` | `.../tools/ip_reputation.py` + `.../adapters/gcp/tor_list_intel.py` | Port/adapter split |
| `backend/tools/actuator.py` | `services/actuator/` (whole service) | Isolation (ADR-006) |
| `backend/Dockerfile` | `services/*/Dockerfile` | Multi-stage, non-root |
| `backend/requirements.txt` | `services/*/pyproject.toml` + `uv.lock` | Reproducible locks |
| `frontend/src/components/*.tsx` | `frontend/src/components/<feature>/*.tsx` | Feature folders |
| `simulation/*.py` | `simulation/src/aegis_sim/*.py` | Installable package, testable |

---

## 3. Ownership (CODEOWNERS suggestion)

| Path | Owner role |
|------|-----------|
| `services/agent-engine/**`, `docs/04_*` | AI/Agents lead |
| `services/api-gateway/**`, `services/actuator/**`, `packages/**` | Backend lead |
| `frontend/**`, `docs/07_*` | Frontend lead |
| `infra/**`, `.github/**`, `docs/10_*` | DevOps lead |
| `simulation/**`, `docs/11_*` | Data/QA lead |
| `docs/12_*`, `firestore.rules` | Security reviewer (all leads) |

---

## 4. Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Python packages | `aegis_<service>` snake_case | `aegis_engine` |
| Python modules | snake_case nouns | `ip_reputation.py` |
| Classes | PascalCase | `EnrichmentAgent`, `FirestoreProfileStore` |
| Ports | `<Thing>` Protocol; adapters `<Tech><Thing>` | `ProfileStore` → `FirestoreProfileStore`, `InMemoryProfileStore` |
| React components | PascalCase file = component | `ThreatGauge.tsx` |
| Hooks | `useCamelCase.ts` | `useInvestigation.ts` |
| Env vars | `AEGIS_<AREA>_<NAME>` | `AEGIS_MODEL_SPECIALIST` |
| Cloud Run services | `aegis-<service>` | `aegis-agent-engine` |
| Service accounts | `sa-<service>@` | `sa-actuator@` |
| Firestore collections | snake_case plural | `user_profiles` |
| BigQuery tables | snake_case | `investigation_results` |
| Branches | `<type>/<ticket>-<slug>` | `feat/AEG-12-threat-gauge` |
