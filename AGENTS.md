# AGENTS.md — Aegis AI Fraud Ops
## Permanent Rules for AI Coding Assistants

**Project:** Aegis AI Fraud Ops  
**Specification baseline:** v1.0 in `docs/`  
**Superseded specification:** `PROJECT_SPEC.md` (v0)  
**Applies to:** Antigravity, Cursor, Windsurf, Claude Code, GitHub Copilot, and other AI coding assistants  
**Purpose:** Maintain architectural consistency, prevent hallucinated implementation, protect security invariants, and ensure that every development task is traceable and verifiable.

---

# 1. Core Mission and Operating Principles

Aegis AI Fraud Ops is an explainable, real-time transaction fraud investigation platform built around deterministic enrichment, Gemini-powered specialist agents, policy-controlled actions, and a real-time Security Operations Center (SOC) dashboard.

The system must support the approved fraud scenarios, including:

- Account takeover and impossible travel.
- Transaction velocity anomalies and structuring.
- Suspicious network and IP reputation signals.
- Unusual merchant categories and monetary behavior.
- Evidence-backed risk assessment and investigation.
- Deterministic policy enforcement and authorized containment.
- Real-time investigation telemetry and analyst review.

The primary architectural principle is:

**Deterministic code establishes facts, LLMs interpret evidence, and deterministic policy controls consequential actions.**

All development must optimize for correctness, security, explainability, reproducibility, and successful demonstration of the approved requirements.

Do not optimize for the amount of code generated or the number of AI agents created.

## 1.1 Non-negotiable priorities

1. Preserve the approved project mission and architecture.
2. Never invent technical facts, repository contents, or verification results.
3. Never weaken security controls to make a demonstration work.
4. Never allow an LLM to independently execute consequential actions.
5. Implement the smallest complete change that satisfies the task.
6. Test behavior, boundaries, failure paths, and regressions.
7. Record development progress and verification evidence.
8. Ask for approval when a decision affects architecture, security, scope, cost, or irreversible actions.
9. Keep the project runnable in mock mode without cloud credentials.
10. Never report unverified work as complete.

---

# 2. Source of Truth and Mandatory Reading

## 2.1 Specification hierarchy

Follow this authority order:

1. Explicitly approved security and safety constraints.
2. Approved v1.0 architecture decisions and specifications in `docs/`.
3. API contracts, schemas, agent specifications, and feature requirements.
4. The current task's acceptance criteria and approved decisions.
5. Existing implementation and reproducible test evidence.
6. AI-generated suggestions.

`PROJECT_SPEC.md` is the superseded v0 baseline.

When the v0 specification conflicts with the newer approved specifications in `docs/`, the newer specifications take precedence.

Do not silently resolve contradictions between two current specifications. Record the conflict and request clarification when it affects implementation, security, or architecture.

## 2.2 Required reading at the start of a task

Before modifying code, inspect:

1. `AGENTS.md`
2. `README.md`
3. `docs/01_PROJECT_ANALYSIS.md`
4. `docs/02_ARCHITECTURE.md`
5. `docs/04_AGENTS_SPEC.md`
6. `docs/05_FEATURES_REQUIREMENTS.md`
7. `docs/14_ROADMAP_TASKS.md`
8. `Taskfile.yml`
9. `.env.example`
10. Git status and the relevant existing implementation.

Then read the specifications relevant to the task:

| Task area | Required documentation |
|---|---|
| AI model configuration and prompts | `docs/03_AI_MODEL_STRATEGY.md`, `docs/04_AGENTS_SPEC.md` |
| Backend and agent implementation | `docs/06_BACKEND_SPEC.md`, `docs/04_AGENTS_SPEC.md` |
| Frontend and dashboard | `docs/07_FRONTEND_SPEC.md` |
| Schemas, APIs, Firestore, BigQuery | `docs/08_DATA_SCHEMAS_API.md` |
| Directory structure and module boundaries | `docs/09_REPOSITORY_STRUCTURE.md` |
| CI/CD, infrastructure, deployment | `docs/10_DEVOPS_AUTOMATION.md` |
| Unit tests, integration tests, evaluation | `docs/11_TESTING_EVALUATION.md` |
| Security, privacy, and compliance | `docs/12_SECURITY_COMPLIANCE.md` |
| Coding standards and Git workflow | `docs/13_CODING_STANDARDS.md` |
| Task dependencies and release plan | `docs/14_ROADMAP_TASKS.md` |

If `development/CURRENT_STATE.md`, `development/DEVELOPMENT_LOG.md`, or `development/MODEL_REGISTER.md` exists, consult the relevant records before starting.

Do not assume a referenced file exists. Inspect the repository and report missing files or incomplete setup.

## 2.3 Repository inspection rules

Before editing:

- Inspect the current directory structure.
- Search for existing implementations before creating new ones.
- Read the relevant interfaces and tests.
- Inspect dependency versions and lockfiles.
- Check configuration and environment-variable definitions.
- Identify consumers of any interface being modified.
- Run `git status --short`.
- Preserve existing user modifications.

Never infer that an implementation exists solely because it is described in a specification.

---

# 3. Permanent IDE Model-Selection Rules

The IDE coding model and the application's runtime models are separate concerns.

The IDE model assists with repository analysis, implementation, debugging, and review. The runtime models perform fraud analysis within the deployed application.

Changing the IDE model must never silently change application model configuration.

## 3.1 Select the model by task complexity

### Tier A — High-reasoning model

Use for:

- Architecture and distributed-system decisions.
- Security and threat-model reviews.
- Complex multi-file debugging.
- Policy engine and actuator changes.
- Authentication and authorization.
- Model orchestration and fallback design.
- Cross-service schema or contract changes.
- Difficult integration failures.
- Final release and regression reviews.

The model must inspect the actual implementation and relevant specifications before recommending changes.

### Tier B — Strong coding model

Use for:

- FastAPI endpoints.
- Python domain logic and adapters.
- Google ADK agent implementation.
- React and TypeScript features.
- API contract integration.
- Database access layers.
- Unit and integration tests.
- Routine refactoring within approved boundaries.

### Tier C — Fast, economical model

Use for:

- Formatting and lint fixes.
- Small documentation changes.
- Straightforward repetitive components.
- Simple test scaffolding.
- Minor, isolated bug fixes.
- Summarizing verified test results.

Do not delegate unresolved security decisions, architecture redesign, or complex policy failures to a low-cost model without independent review.

## 3.2 Recommended model workflow

Use a strong coding model as the normal implementation model, a high-reasoning model for difficult or security-sensitive work, and an economical model for routine tasks.

Choose the actual models from those currently available in the IDE. Model names, availability, capabilities, and lifecycle status must be verified rather than assumed.

When selecting a model, consider:

- Correctness on the project's representative tasks.
- Ability to inspect and modify multiple files safely.
- Tool execution and debugging reliability.
- Adherence to project instructions.
- Context capacity for the current task.
- Cost and latency.
- Availability and lifecycle stability.

Do not switch models repeatedly during a single task without a clear reason.

If a model fails repeatedly, document the failure, switch to a suitable alternative, and independently verify the resulting implementation.

## 3.3 Runtime Gemini model governance

All application model IDs must come from approved settings and environment variables using the project's `AEGIS_MODEL_*` configuration.

The approved model roles are:

- Specialist agents: the configured lightweight Gemini model.
- Orchestrator: the configured Gemini Flash model.
- Deep review: the configured Gemini Pro model for approved asynchronous cases.

Do not hard-code runtime model IDs in agent implementation files.

Do not use retired `gemini-1.5-*` models or the deprecated `vertexai.generative_models` API.

Use the approved `google-genai` and `google-adk` integration described in the project specifications.

Before enabling a runtime model:

1. Inspect the current model configuration.
2. Run `task ai:models` where the environment supports it.
3. Verify model availability for the configured project and location.
4. Check supported structured-output capabilities.
5. Run the relevant integration and golden tests.
6. Record the result and exact model identifier.
7. Document any approved fallback.

Never silently switch to a different model because of an API error or model retirement.

The permitted degradation path is the explicitly configured primary model, approved fallback, and deterministic verdict path, with each transition handled and logged according to the specifications.

## 3.4 Model register

Maintain `development/MODEL_REGISTER.md` when the development logging structure is established.

Record:

- Model provider and exact identifier, when available.
- Purpose: IDE coding, review, or application inference.
- Approval status.
- Evaluation date.
- Representative tasks evaluated.
- Test outcomes.
- Measured latency and cost, if available.
- Known limitations.
- Approved fallback.
- Reason for selection.

Never invent model benchmark results or claim that a model is superior without supporting evidence.

---

# 4. Mandatory Task Lifecycle

Every implementation task must follow the same workflow.

## Phase 1 — Understand

- Read the applicable instructions and specifications.
- Inspect the current implementation and Git status.
- Identify task dependencies and affected modules.
- Identify existing tests and required acceptance criteria.
- Detect specification conflicts and unresolved assumptions.

## Phase 2 — Plan

Before making substantial changes, report:

- Task ID.
- Objective.
- Relevant specifications.
- Files and interfaces likely to change.
- Dependencies.
- Proposed implementation.
- Security and regression risks.
- Verification plan.
- Explicit exclusions.

Keep the plan proportional to the task. A minor documentation fix does not require an extensive architecture proposal.

For security-sensitive changes, architecture changes, destructive actions, dependency additions, or cloud infrastructure modifications, obtain explicit approval before proceeding.

## Phase 3 — Implement

- Make the smallest complete change.
- Follow existing architecture and naming conventions.
- Preserve unrelated changes.
- Add tests alongside behavior changes.
- Keep changes focused on the approved objective.
- Do not add unrequested features.

## Phase 4 — Verify

- Run applicable linting and formatting checks.
- Run type checking.
- Run unit tests.
- Run contract and integration tests where relevant.
- Run security and regression checks where relevant.
- Inspect the final diff.
- Investigate failures rather than hiding them.

## Phase 5 — Record

- Update the development log.
- Update current project state.
- Update task status.
- Update the roadmap if its status changed.
- Update specifications or ADRs when approved decisions change.
- Record actual verification results.

## Phase 6 — Report

Report the outcome, evidence, unresolved issues, and next task.

Do not start another unrelated task before the current task has been reported.

---

# 5. Anti-Hallucination and Technical Verification Rules

## 5.1 Technical facts must be verified

Never invent:

- Files, modules, classes, or functions.
- Package APIs or SDK methods.
- Dependency versions or compatibility.
- Environment variables or configuration options.
- Task names or command-line arguments.
- Cloud resources or deployment status.
- Database collections or fields.
- Test results or benchmark metrics.
- Evidence IDs, citations, or security findings.

Verify claims using the actual repository, installed dependencies, lockfiles, official documentation, configuration, or executable tests.

If verification is unavailable, label the claim `UNVERIFIED`.

If a required fact cannot be established, explain the uncertainty and stop the affected work when necessary.

## 5.2 No fabricated execution results

Never claim:

- A command passed without an actual successful result.
- A service is running without evidence.
- A deployment succeeded without deployment evidence.
- A model is available without verification.
- A benchmark target was met without measured results.
- A feature is complete merely because code was generated.

Clearly distinguish `NOT RUN`, `BLOCKED`, `FAILED`, and `PASSED`.

## 5.3 Documentation and code must agree

If the implementation contradicts the approved specification:

1. Identify the discrepancy.
2. Determine whether the implementation or specification is outdated.
3. Check for an approved decision or existing ADR.
4. Request approval when a material decision is needed.
5. Update code and documentation consistently after approval.

Do not silently modify the specification to justify incorrect code.

## 5.4 External information

Use official documentation for technical API and SDK questions when repository evidence is insufficient.

Pin or constrain dependencies according to the existing project standards.

Do not introduce a dependency merely because an AI model recommends it.

Verify the dependency's compatibility, maintenance status, security implications, licensing requirements where applicable, and need for the project.

---

# 6. Non-Negotiable Architecture Rules

## 6.1 Hexagonal architecture

Maintain the dependency direction:

`api → application → domain`

Adapters implement ports defined by the appropriate inner layers.

Rules:

- `domain/` must not import FastAPI.
- `domain/` must not import Google Cloud SDKs.
- `domain/` must not import adapter implementations.
- Business logic must remain independent of external infrastructure.
- Application services coordinate use cases through interfaces.
- Adapters implement external system integrations.
- Dependency injection belongs in the approved bootstrap or application composition layer.
- Avoid circular imports and unnecessary abstraction layers.

## 6.2 Microservice boundaries

Preserve the approved responsibilities:

### API gateway

- HTTP request validation.
- Authentication and rate limiting where specified.
- Request normalization.
- Idempotency handling.
- Synchronous or asynchronous dispatch.
- Structured error responses.

### Agent engine

- Intake and enrichment orchestration.
- Triage and specialist execution.
- Evidence correlation.
- Policy evaluation.
- Closeout and telemetry emission.

### Actuator

- Approved lock, unlock, block, and alert operations.
- Independent authorization checks.
- Idempotency.
- Auditing.
- Least-privilege execution.

Do not move consequential action execution into the gateway, frontend, or LLM specialist agents.

## 6.3 Ports and adapters

Every external dependency must have an appropriate interface and mock adapter.

This includes relevant dependencies such as:

- Profiles and behavioral baselines.
- IP intelligence.
- Telemetry storage.
- Results storage.
- Actuator execution.
- External data access.

`AEGIS_ADAPTER_MODE=mock` must support offline development and testing without GCP credentials.

Mock behavior must be deterministic, explicitly configured, and representative of the interface contract.

Do not make tests secretly depend on live cloud services.

## 6.4 Dependency injection and lifecycle

Do not instantiate GCP clients at module import time.

Create clients through the approved bootstrap or application lifespan and inject them into dependent services.

Ensure resources are initialized, reused, and closed according to their lifecycle.

Use explicit configuration and predictable failure handling.

---

# 7. Deterministic Fraud Logic and AI Agent Rules

## 7.1 Deterministic facts

Compute the following in Python:

- Z-scores.
- Haversine distance.
- Travel speed and impossible-travel checks.
- Transaction velocity windows.
- Structuring and near-threshold aggregation.
- Deterministic base risk scores.
- Hard-rule risk floors.
- Policy thresholds and action eligibility.

Never delegate mathematical calculations or final authorization to an LLM.

Use explicit units, configurable thresholds where specified, boundary tests, and documented formulas.

## 7.2 LLM authority boundaries

LLMs may:

- Interpret precomputed features.
- Identify patterns in supplied evidence.
- Produce structured findings.
- Correlate specialist outputs.
- Generate explanations.
- Produce asynchronous review narratives.

LLMs must not:

- Execute account lockouts.
- Block transactions directly.
- Dispatch alerts directly.
- Grant themselves permissions.
- Change policy thresholds.
- Override deterministic hard-rule floors.
- Invent supporting evidence.
- Bypass schema validation.

Actuator tools such as `execute_account_lockout`, `block_transaction`, and `dispatch_alert` may be invoked only through the approved deterministic `PolicyAgent` path.

Never register these actuator tools on an `LlmAgent`.

## 7.3 Bounded score adjustment

The orchestrator's `score_adjustment` must remain within:

`-10 <= score_adjustment <= 10`

Apply the bound in deterministic code.

The adjustment must never cross a hard-rule floor or violate the approved scoring and risk-band policy.

Validate types, numeric ranges, missing values, and unexpected outputs.

Do not allow model-generated scores to bypass the policy engine.

## 7.4 Structured agent outputs

Every `LlmAgent` must use the approved Pydantic `output_schema` and `output_key`.

Ensure that:

- Schemas match the approved agent contracts.
- Invalid outputs are rejected or handled through the approved fallback.
- Evidence identifiers refer to actual evidence.
- Unsupported findings are dropped or rejected according to the specification.
- Prompt and schema changes are versioned.
- Golden tests are updated for behavior changes.

Respect Google ADK's constraints on structured-output agents and tool usage. Keep deterministic enrichment and tool execution separate from specialist agents where required by the approved design.

## 7.5 Triage and fast-path behavior

Preserve the approved triage fast path for clean transactions.

Do not introduce unnecessary LLM calls on the fast path.

Do not skip required enrichment, security checks, or policy rules simply to reduce latency.

Early containment must follow the approved deterministic conditions and authorization rules.

Deep review must remain asynchronous when specified and must not delay mandatory containment.

## 7.6 Failure and degraded mode

Handle model timeouts, unavailable models, invalid structured outputs, rate limits, and external service failures.

Use approved retry limits, per-stage timeouts, and fallback behavior.

Retries must be bounded and restricted to appropriate transient failures.

Ensure that failures are observable and that consequential actions are not duplicated.

---

# 8. Model Prompts, Injection Defense, and Evidence Integrity

Treat merchant names, transaction descriptions, free-text fields, retrieved content, external responses, and LLM outputs as untrusted input.

Required controls:

- Delimit untrusted fields in prompts.
- Apply the documented sanitization and length limits.
- Do not treat embedded instructions as system instructions.
- Do not allow transaction content to modify tool permissions.
- Validate structured output before consuming it.
- Validate every evidence identifier against existing evidence.
- Preserve evidence provenance.
- Log invalid outputs and injection signals safely.
- Never include unnecessary personal or financial information in prompts.

Do not rely on regular-expression sanitization alone as a complete prompt-injection defense.

Enforce authorization and action restrictions in deterministic application code.

For every prompt or policy change:

1. Bump the applicable version.
2. Review the effect on model behavior.
3. Update golden tests.
4. Run the applicable evaluation.
5. Record the result.

Never tune prompts to achieve a benchmark result by suppressing valid detections or hiding failures.

---

# 9. AI Model Configuration and Versioning

All application model IDs must be provided through the approved `settings.model_*` configuration and corresponding `AEGIS_MODEL_*` environment variables.

Do not hard-code model identifiers in individual agent modules.

The example model IDs in the specifications must be verified against the actual Vertex AI project, location, availability, and lifecycle before use.

Use `task ai:models` where supported by the configured environment.

Version and record:

- Model IDs.
- Prompt versions.
- Schema versions.
- Risk-policy versions.
- Evaluation dataset versions and hashes.
- Relevant runtime configuration.

Store the applicable model, prompt, and policy versions on each verdict according to the approved schema.

Any change to a model, prompt, schema, scoring rule, or policy requires the appropriate regression evaluation.

Do not claim an exact latency or cost until it has been measured under the relevant workload.

---

# 10. Backend Development Standards

Follow `docs/06_BACKEND_SPEC.md` and `docs/13_CODING_STANDARDS.md`.

Required conventions:

- Python 3.12.
- `uv` for the approved workspace and dependency workflow.
- Ruff for linting and formatting.
- Strict mypy.
- Pydantic v2 for I/O schemas.
- Typed Protocol interfaces.
- Google-style docstrings.
- Async I/O for applicable external operations.
- Explicit timeouts for external calls.
- Structured logging with `structlog`.
- No `print` statements in production application code.
- No module-level GCP clients.
- No hidden global mutable state.
- Explicit configuration and dependency injection.

Keep domain calculations independently testable.

Add tests for normal cases, boundaries, invalid inputs, and failures.

Do not use broad exception handling that hides failures or converts every exception into a successful response.

Do not add `Any` to domain interfaces.

Use typed error handling and the project's documented API error format.

---

# 11. Frontend Development Standards

Follow `docs/07_FRONTEND_SPEC.md`, `docs/08_DATA_SCHEMAS_API.md`, and `docs/13_CODING_STANDARDS.md`.

Required conventions:

- React 18.
- Vite.
- Strict TypeScript.
- Tailwind CSS v4 and approved design tokens.
- Approved motion and animation libraries.
- ESLint and Prettier.
- Vitest and React Testing Library.
- Playwright for end-to-end testing where configured.
- Accessible interactive elements.
- Reduced-motion support.
- Clear loading, empty, and error states.

Use generated contract types as the authoritative API shapes.

Do not manually maintain duplicate API interfaces when generated types are available.

Do not use TypeScript `any`.

Validate API responses and handle failures explicitly.

Keep visual components separate from data-access and application logic where appropriate.

Preserve the approved Midnight SOC design system.

The dashboard must not directly write to Firestore.

Firestore writes must remain server-side, and the frontend must mutate data through the approved REST API.

Frontend Firestore access is read-only through the approved listener pattern.

Do not fabricate live telemetry, investigation results, or backend status in production-facing functionality.

Clearly distinguish mock demonstration data from live service responses.

---

# 12. API, Schema, and Data Contract Rules

Follow `docs/08_DATA_SCHEMAS_API.md`.

Before changing a schema or API:

1. Identify all producers and consumers.
2. Inspect the current version and compatibility requirements.
3. Define the intended contract change.
4. Add or update validation and contract tests.
5. Implement the approved change.
6. Run `task schemas:export` when schemas change.
7. Regenerate TypeScript contract types.
8. Verify frontend and backend compatibility.
9. Update documentation and version metadata.

Do not modify generated files manually unless the repository explicitly designates them as editable sources.

Do not introduce unversioned breaking changes.

Validate incoming requests and outgoing responses against the approved contracts.

Preserve idempotency and stable error handling.

Use explicit data types, timestamps, units, enums, and nullability.

Do not silently reinterpret monetary values, time windows, geographic coordinates, or risk bands.

---

# 13. Security and Privacy Rules

Follow `docs/12_SECURITY_COMPLIANCE.md`.

## 13.1 Secrets

Never commit:

- `.env` files containing secrets.
- Service-account keys.
- API tokens.
- Passwords.
- Private certificates.
- Authentication cookies.
- Other credentials.

Only use `.env.example` for safe configuration templates.

Use the approved secret-management mechanism for deployments.

Run the configured secret scanning tools when available.

Never print secrets into terminal output, logs, reports, prompts, or development records.

## 13.2 Data protection

Use synthetic data for hackathon development and evaluation.

Do not ingest real customer data unless explicitly approved through the applicable security and privacy process.

Do not send names, emails, phone numbers, payment-card details, or other unnecessary personal information to LLMs.

Apply the documented masking, retention, and pseudonymization rules.

Never log full payment-card numbers, CVV values, or other prohibited card data.

## 13.3 Authentication and authorization

Any new public endpoint must have:

- Appropriate authentication.
- Rate limiting.
- Input validation.
- Authorization checks where applicable.
- Tests for unauthorized requests, including 401/403 as appropriate.
- Rate-limit tests, including 429.
- Safe error responses.
- Relevant audit and telemetry behavior.

Do not expose internal actuator endpoints publicly.

Preserve least-privilege service accounts and separate service responsibilities.

## 13.4 Firestore and cloud security

Preserve server-side write restrictions.

Do not weaken Firestore security rules, IAM permissions, authentication, or audit controls.

Do not create public cloud resources or change deployment permissions without authorization.

Any change involving IAM, Firestore rules, authentication, actuator permissions, or secrets requires explicit security review.

---

# 14. Observability and Telemetry

Follow the telemetry contracts in the approved specifications.

Every applicable agent step must emit a `TelemetryEvent` through `TelemetryEmitter`.

Telemetry must preserve:

- Transaction and investigation correlation.
- Trace identifiers where applicable.
- Ordered sequence numbers.
- Agent or pipeline stage.
- Event type and relevant status.
- Validated, masked evidence references.
- Model, prompt, and policy versions where specified.

Mask personal information before writing telemetry.

Do not emit secrets, unmasked sensitive data, or unrestricted raw prompts.

Preserve ordering and idempotency requirements.

Test telemetry behavior, including sequence ordering, masking, storage failure, and missing or malformed event data where applicable.

Do not claim real-time telemetry works until the actual configured storage and listener flow has been verified.

---

# 15. Testing and Quality Gates

Follow `docs/11_TESTING_EVALUATION.md` and `docs/13_CODING_STANDARDS.md`.

## 15.1 Required testing layers

Use the applicable combination of:

- Unit tests.
- Domain boundary tests.
- Property-based tests.
- API contract tests.
- Adapter tests.
- Integration tests.
- Agent golden tests.
- Security and adversarial tests.
- Frontend component tests.
- End-to-end tests.
- Performance and load tests.

Do not introduce live cloud dependencies into ordinary unit tests.

Use mocks and emulators according to the existing project configuration.

## 15.2 Coverage requirements

Preserve the specified minimum domain coverage of 95%.

Follow the approved overall coverage gate in the testing specification and coding standards.

Do not manipulate coverage by removing meaningful assertions or excluding relevant production modules.

Coverage is a quality signal, not a substitute for meaningful test cases.

## 15.3 Required evaluation behavior

The approved benchmark contains 2,000 balanced cases: 1,500 benign cases, including hard negatives, and 500 adversarial cases.

The approved targets are:

- Accuracy greater than 98%.
- False-positive rate below 1.5%.
- Average end-to-end latency below 2.8 seconds.
- p95 latency below 4 seconds.
- Evidence identifiers present and valid for all applicable verdicts.

These are acceptance targets, not guaranteed results.

Use the versioned evaluation dataset and preserve its hash and metadata.

Report actual measured values.

Do not change labels, remove difficult cases, or weaken targets simply to produce a passing result.

Investigate false positives, false negatives, invalid outputs, and latency regressions.

---

# 16. Command Execution Rules

Inspect `Taskfile.yml` and verify task definitions before assuming a command exists.

The project command set includes the following documented commands:

```bash
task setup
task dev
task lint
task typecheck
task test
task test:integration
task schemas:export
task ai:models
task sim:generate
task sim:redteam
```

Use additional documented tasks for golden tests, end-to-end testing, deployment, and demonstration preparation when they exist and are relevant.

Do not invent Taskfile targets.

Do not assume all commands can run without cloud credentials, emulators, installed dependencies, or environment configuration.

Prefer mock mode for offline development.

Before executing a command, understand whether it:

- Reads files.
- Modifies files.
- Installs packages.
- Accesses external services.
- Changes cloud infrastructure.
- Deploys an application.
- Performs an irreversible action.

Obtain explicit approval for destructive operations, consequential cloud changes, or deployment actions requiring authorization.

Do not run destructive commands merely to resolve a failed test.

---

# 17. Git and Change Management

Follow `docs/13_CODING_STANDARDS.md`.

## 17.1 Preserve user changes

Always inspect Git status before editing.

Never discard unrelated modifications.

Do not run `git reset --hard`, force-push, delete unrelated files, rewrite history, or overwrite uncommitted work without explicit authorization.

Use focused patches and review the final diff.

## 17.2 Branches and commits

Follow the repository's trunk-based workflow and short-lived branches.

Use the documented branch naming pattern:

- `feat/AEG-12-threat-gauge`
- `fix/AEG-31-travel-exemption`
- `chore/...`
- `docs/...`

Use Conventional Commits, for example:

```text
feat(engine): add structuring detector
fix(policy): preserve impossible-travel risk floor
test(agents): add malformed-output cases
docs(architecture): record approved decision
```

Follow the documented pull-request size, review, ownership, and merge requirements.

Do not commit, push, merge, tag, or deploy without the required authorization.

## 17.3 Final diff review

Before declaring a task complete, inspect:

- All modified files.
- Unintended formatting or generated-file changes.
- Missing tests.
- Removed comments or docstrings unrelated to the task.
- Secret or PII exposure.
- Dependency and lockfile changes.
- Contract compatibility.
- Architectural boundary violations.

---

# 18. Development Logging and Project Memory

Maintain a version-controlled development history so that the project does not depend on the conversational memory of any one AI model.

Use the following files where they do not already exist:

```text
development/
├── CURRENT_STATE.md
├── DEVELOPMENT_LOG.md
├── MODEL_REGISTER.md
├── TASK_TEMPLATE.md
├── decisions/
└── reports/
```

Check the existing repository structure before creating new files.

## 18.1 CURRENT_STATE.md

Maintain a concise snapshot of:

- Current project phase.
- Current task ID.
- Last verified completed task.
- Current branch or commit, when available.
- Verified working components.
- Failed or blocked checks.
- Open decisions.
- Known limitations.
- Immediate next task and dependencies.

Do not list untested functionality as verified.

## 18.2 DEVELOPMENT_LOG.md

Record each task chronologically:

- Task ID.
- Date and time, where available.
- Objective.
- Specifications consulted.
- Actual IDE model identifier, when available.
- Files changed.
- Implementation summary.
- Commands executed.
- Actual test results.
- Decisions and assumptions.
- Known limitations.
- Next action.

Preserve historical records. Record corrections as new entries rather than silently rewriting previous results.

## 18.3 MODEL_REGISTER.md

Track the models used for development and runtime inference, including verified identifiers, roles, evaluation outcomes, limitations, and approval status.

Do not mix IDE model settings with application runtime model settings.

## 18.4 Roadmap status

Use the task IDs and dependencies in `docs/14_ROADMAP_TASKS.md`.

Update task statuses only when supported by evidence.

A task is not complete because its code was generated. The relevant acceptance criteria and verification results must support the status.

---

# 19. Architecture Decision Records

When an approved architectural change is necessary, create an ADR in `docs/adr/` if that location is consistent with the existing repository.

Use a sequential filename, for example:

`docs/adr/ADR-0001-approved-model-fallback.md`

Each ADR should contain:

- Title and status.
- Date.
- Context and problem.
- Decision.
- Alternatives considered.
- Reasons for the decision.
- Security implications.
- Performance and cost implications.
- Affected modules and specifications.
- Migration or rollback considerations.

Do not create an ADR to justify an unapproved change after the fact.

Update the relevant architecture or implementation specification after approval.

---

# 20. Scope Control and Priority Rules

Follow the MoSCoW priorities in `docs/05_FEATURES_REQUIREMENTS.md` and `docs/14_ROADMAP_TASKS.md`.

Prioritize:

1. Must-have requirements and foundational dependencies.
2. Correctness of deterministic domain logic.
3. Secure agent execution and policy enforcement.
4. API contracts and mock adapters.
5. End-to-end integration.
6. Dashboard demonstration scenarios.
7. Benchmarking, security hardening, and release readiness.
8. Should-have and Could-have improvements only when prerequisites and deadlines permit.

Do not add optional features while mandatory tasks remain blocked.

Do not refactor unrelated modules for aesthetic reasons.

If a task expands beyond its approved scope, stop and request approval for the additional work.

---

# 21. Error Handling and Recovery

When a command, test, model request, or integration fails:

1. Capture the actual error.
2. Identify the affected component.
3. Reproduce the issue when practical.
4. Inspect the relevant code and configuration.
5. Determine whether the failure is caused by implementation, environment, dependencies, permissions, or external availability.
6. Apply the smallest justified fix.
7. Add a regression test when appropriate.
8. Re-run the failed check and relevant dependent tests.
9. Record the result.

Do not repeatedly apply speculative fixes.

Do not suppress exceptions, disable failing tests, or substitute fabricated success responses.

If the cause remains unknown, report the blocker and the evidence collected.

---

# 22. Definition of Done

A task may be marked `COMPLETE` only when all applicable requirements are satisfied.

1. The approved acceptance criteria are met.
2. The implementation respects architecture and security constraints.
3. Required tests have actually executed and passed.
4. Domain coverage and relevant quality gates remain satisfied.
5. Contract types are regenerated where required.
6. Prompt and policy versions are updated where required.
7. The final diff has been reviewed.
8. Relevant documentation and development logs are updated.
9. No unresolved critical security issue is introduced.
10. Required code review and CI checks are satisfied.
11. Deployment and smoke tests are complete when deployment is part of the task.
12. The actual outcome is reported accurately.

Use these statuses:

- `PLANNED`: not started.
- `IN_PROGRESS`: implementation underway.
- `BLOCKED`: cannot proceed safely or correctly.
- `PARTIALLY_COMPLETE`: some criteria remain unmet.
- `IMPLEMENTED`: code exists but verification is incomplete.
- `VERIFIED`: applicable local checks passed.
- `COMPLETE`: all applicable acceptance and delivery criteria are satisfied.

Do not use `COMPLETE` as a substitute for `VERIFIED`, or `VERIFIED` as a substitute for `DEPLOYED`.

---

# 23. Mandatory Final Response Format

After each implementation task, report:

```text
TASK ID:
OBJECTIVE:
SPECIFICATIONS CONSULTED:
PLAN APPROVED:
FILES CHANGED:
IMPLEMENTATION SUMMARY:

VERIFICATION COMMANDS:
ACTUAL RESULTS:
TESTS NOT RUN OR BLOCKED:

SECURITY REVIEW:
REGRESSION REVIEW:
DOCUMENTATION UPDATED:
DEVELOPMENT LOG UPDATED:

UNRESOLVED ISSUES:
KNOWN LIMITATIONS:
FINAL STATUS:
NEXT TASK:
```

Be concise and evidence-based.

Do not claim that a feature works unless the implementation and verification results support that statement.

If the task is blocked, explain the precise blocker and the minimum action needed to resolve it.

---

# 24. Final Instruction

The project specifications define the intended system.

The implementation must respect those specifications.

Deterministic code owns facts, policy, authorization, and consequential actions.

LLMs assist with evidence interpretation and explanation but never bypass approved controls.

Tests establish what has been verified.

Development records preserve what actually happened.

Human approval governs material changes in architecture, scope, security, and irreversible actions.

**Never sacrifice correctness, security, or traceability to generate code faster.**