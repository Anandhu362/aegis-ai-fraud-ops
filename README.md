# 🛡️ Aegis AI Fraud Ops

> **Real-time, explainable, multi-agent fraud defense for Banking, Financial Services & Insurance (BFSI).**
> Built for the **Google Cloud AI Builder Cup 2026** (BFSI Track — Intelligent Risk, Fraud & Financial Experiences).

Aegis scores each incoming card or payment transaction with a group of specialised AI agents built on **Google ADK + Gemini on Vertex AI**:

- a **Behavioral Analyst** (statistical anomalies),
- a **Threat Intelligence** agent (network, Tor/VPN, impossible travel),
- an **Orchestrator** that combines their evidence into a single **0–100 Threat Score**.

A **deterministic policy engine** then decides what happens: allow, send for review, block the transaction, or lock the account. Every reasoning step streams live to a **React SOC dashboard** through **Cloud Firestore**.

---

## 📚 Documentation Index

| # | Document | Purpose |
|---|----------|---------|
| 0 | [PROJECT_SPEC.md](./PROJECT_SPEC.md) | Original v0 hackathon spec (kept for reference; **superseded by `docs/`**) |
| 1 | [01_PROJECT_ANALYSIS.md](./docs/01_PROJECT_ANALYSIS.md) | Problem, solution, judging alignment, **gap analysis of v0 spec** |
| 2 | [02_ARCHITECTURE.md](./docs/02_ARCHITECTURE.md) | System & microservice architecture, data flow, ADRs, resilience |
| 3 | [03_AI_MODEL_STRATEGY.md](./docs/03_AI_MODEL_STRATEGY.md) | Gemini model selection per agent, SDKs, latency & cost budget |
| 4 | [04_AGENTS_SPEC.md](./docs/04_AGENTS_SPEC.md) | Agent hierarchy, prompts, tools, risk-scoring algorithm, policy |
| 5 | [05_FEATURES_REQUIREMENTS.md](./docs/05_FEATURES_REQUIREMENTS.md) | Feature catalog, functional & non-functional requirements |
| 6 | [06_BACKEND_SPEC.md](./docs/06_BACKEND_SPEC.md) | Backend services, layering, endpoints, config, code skeletons |
| 7 | [07_FRONTEND_SPEC.md](./docs/07_FRONTEND_SPEC.md) | Dashboard UX, design system, components, realtime data flow |
| 8 | [08_DATA_SCHEMAS_API.md](./docs/08_DATA_SCHEMAS_API.md) | API contracts, Firestore, BigQuery, Pub/Sub schemas |
| 9 | [09_REPOSITORY_STRUCTURE.md](./docs/09_REPOSITORY_STRUCTURE.md) | Monorepo layout & ownership of every folder/file |
| 10 | [10_DEVOPS_AUTOMATION.md](./docs/10_DEVOPS_AUTOMATION.md) | Environments, CI/CD, IaC, IAM, automated & scheduled tasks |
| 11 | [11_TESTING_EVALUATION.md](./docs/11_TESTING_EVALUATION.md) | Test strategy, red-team evaluation, metric definitions |
| 12 | [12_SECURITY_COMPLIANCE.md](./docs/12_SECURITY_COMPLIANCE.md) | Threat model, IAM, PII, LLM safety, BFSI compliance |
| 13 | [13_CODING_STANDARDS.md](./docs/13_CODING_STANDARDS.md) | Code quality rules, Git workflow, Definition of Done |
| 14 | [14_ROADMAP_TASKS.md](./docs/14_ROADMAP_TASKS.md) | Hackathon sprint plan, task board, demo script, future roadmap |
| — | [AGENTS.md](./AGENTS.md) | Rules for AI coding assistants working in this repo |

**Suggested reading order:** 01 → 02 → 04 → 03 → 08 → 06 → 07 → 09 → 10 → 11 → 12 → 13 → 14.

---

## 🧱 Tech Stack (at a glance)

| Layer | Technology |
|-------|-----------|
| Agents | Google **ADK** (`google-adk`), **Gemini** via Vertex AI (`google-genai` SDK) |
| Backend | Python 3.12, FastAPI, Pydantic v2, asyncio, `uv` |
| Data | BigQuery (history & analytics), Cloud Firestore (realtime state), Pub/Sub (event bus) |
| Frontend | React 18, Vite, TypeScript (strict), Tailwind CSS v4, Firebase JS SDK, Motion |
| Platform | Cloud Run (services + jobs), Firebase Hosting, Secret Manager, Artifact Registry, Cloud Scheduler |
| Quality | Ruff, mypy, pytest, ESLint, Prettier, Vitest, Playwright, GitHub Actions |

---

## ⚡ Quickstart (once code exists)

```bash
# 1. Bootstrap tooling
task setup                # installs uv, npm deps, pre-commit hooks

# 2. Run everything locally in MOCK mode (no GCP needed)
task dev                  # Firestore emulator + API + agent-engine + dashboard

# 3. Seed synthetic data & run the red-team evaluation
task sim:generate
task sim:redteam

# 4. Deploy (requires gcloud auth)
task deploy:all ENV=demo
```

See [10_DEVOPS_AUTOMATION.md](./docs/10_DEVOPS_AUTOMATION.md) for full details.

---

## 🎯 Hackathon Success Targets

| Metric | Target |
|--------|--------|
| Detection accuracy (balanced eval set) | **> 98 %** |
| False Positive Rate | **< 1.5 %** |
| Avg. end-to-end investigation latency | **< 2.8 s** (p95 < 4 s) |
| Explainability | 100 % of verdicts carry an evidence-linked rationale |
