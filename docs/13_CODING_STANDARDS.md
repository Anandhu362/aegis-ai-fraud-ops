# 13 · Coding Standards & Engineering Workflow

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Enforcement | pre-commit hooks + CI required checks |

---

## 1. Python Standards

| Rule | Detail |
|------|--------|
| Version | Python 3.12; `from __future__ import annotations` is not needed |
| Formatting | `ruff format` (line length 100) |
| Linting | `ruff check` with rule sets `E,F,W,I,N,UP,B,A,C4,SIM,PL,RUF,ASYNC,S,PT,TID` |
| Typing | `mypy --strict`; no `Any` in domain; `typing.Protocol` for ports |
| Docstrings | Google style for all public modules/classes/functions |
| Models | Pydantic v2 `BaseModel` for I/O; `@dataclass(frozen=True, slots=True)` for internal value objects |
| Async | All I/O async; never block the event loop (`asyncio.to_thread` for sync SDKs); always set timeouts |
| Errors | Raise `AegisError` subclasses; never bare `except:`; map to RFC 7807 at the API edge only |
| Logging | `structlog.get_logger()`; **no `print`**; key-value context (`tx_id=…`); never log secrets or raw PII |
| Config | Only via `Settings`; no `os.getenv` outside settings modules |
| Imports | Absolute imports; domain never imports adapters/GCP SDKs (`import-linter` contract) |
| Globals | No module-level clients or mutable globals; build in `bootstrap.py`, inject via FastAPI `Depends` / constructor |
| Tests | `test_<unit>_<behaviour>()`; Arrange-Act-Assert; one behaviour per test; fixtures in `conftest.py` |

```toml
# pyproject.toml (root, excerpt)
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E","F","W","I","N","UP","B","A","C4","SIM","PL","RUF","ASYNC","S","PT","TID"]
ignore = ["PLR0913"]

[tool.ruff.lint.per-file-ignores]
"**/tests/**" = ["S101", "PLR2004"]

[tool.mypy]
strict = true
plugins = ["pydantic.mypy"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = ["integration", "e2e", "real_llm"]
```

---

## 2. TypeScript / React Standards

| Rule | Detail |
|------|--------|
| TS config | `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true` |
| Lint | ESLint flat config: `typescript-eslint/strict-type-checked`, `react-hooks`, `jsx-a11y`, `import/order` |
| Format | Prettier (printWidth 100, singleQuote, trailingComma all) |
| Components | Function components only; one component per file; props typed with `interface XProps`; no default exports except `App` |
| State | Server state in TanStack Query / Firestore hooks; UI state in Zustand; no prop-drilling > 2 levels |
| Side effects | Subscriptions only inside hooks with cleanup |
| Styling | Tailwind utility classes + design tokens; no inline hex colours; shared variants via `cva`/`cn` |
| Types | Generated contract types are the only source for API shapes; `any` is forbidden (`unknown` + narrowing) |
| Accessibility | Every interactive element has an accessible name and a unique `id`/`data-testid` |
| Tests | `*.test.tsx` beside components; test behaviour, not implementation |

---

## 3. Git Workflow

| Item | Convention |
|------|-----------|
| Branching | Trunk-based: short-lived branches off `main`; `main` always deployable to `dev` |
| Branch names | `feat/AEG-12-threat-gauge`, `fix/AEG-31-travel-exemption`, `chore/…`, `docs/…` |
| Commits | **Conventional Commits**: `feat(engine): add structuring detector` |
| PR size | ≤ 400 changed lines (excluding generated); one concern per PR |
| Reviews | ≥ 1 approval; CODEOWNERS for owned paths; security reviewer for `firestore.rules`, IAM, actuator |
| Merge | Squash merge; PR title = conventional commit |
| Releases | Tags `vMAJOR.MINOR.PATCH`; tag → demo deploy; changelog generated from commits |

### PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
```markdown
## What & Why
<!-- Link: AEG-XX -->
## How
## Screenshots / Telemetry sample (UI or agent changes)
## Checklist
- [ ] Tests added/updated (unit + contract where relevant)
- [ ] Docs updated (docs/0X, ADR if architectural)
- [ ] No secrets / PII in code, logs, fixtures
- [ ] Prompt or policy change → version bumped + golden tests updated
- [ ] Schema change → `task schemas:export` run, TS types regenerated
```

---

## 4. Code Review Checklist

- **Correctness:** domain math covered by tests at boundaries; idempotency honoured.
- **Boundaries:** no GCP imports in `domain/`; adapters behind ports.
- **Resilience:** timeouts on every I/O call; failure path emits telemetry and is tested.
- **Security:** inputs validated; no new public endpoints without auth; least privilege preserved.
- **Observability:** logs carry `tx_id`/`trace_id`; new stage gets a span.
- **AI changes:** prompt version bumped; schema-constrained; golden tests pass; no actuator tool on LlmAgents.
- **UI:** reduced-motion respected; contrast AA; IDs stable.

---

## 5. Definition of Done

A task is **Done** when:
1. Code merged to `main` with green CI (lint, types, tests, security, build).
2. Acceptance criteria from [05_FEATURES_REQUIREMENTS](./05_FEATURES_REQUIREMENTS.md) are demonstrably met.
3. Unit coverage for changed domain code ≥ 95 %; overall gates hold.
4. Docs/ADR updated; contracts regenerated if schemas changed.
5. Deployed to `dev` and smoke-tested; telemetry visible in the dashboard where applicable.

---

## 6. Versioning of Non-Code Artefacts

| Artefact | Version location | Bump rule |
|----------|------------------|-----------|
| Prompts | front-matter `version:` in `prompts/*.md` | Any wording change → minor; schema change → major |
| Risk policy | `version:` in `risk_policy.yaml` | Weight/threshold change → minor |
| Eval dataset | `eval_set_vN.jsonl` + SHA-256 in metadata | Any change → new N |
| Contracts | `schema` attribute (`tx_ingested.v1`) | Breaking change → new version, both served during migration |
