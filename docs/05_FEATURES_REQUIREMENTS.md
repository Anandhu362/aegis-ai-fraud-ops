# 05 · Features & Requirements

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Priority scheme | **MoSCoW**: **M**ust (hackathon MVP), **S**hould (if time), **C**ould (stretch), **W**on't (future) |

---

## 1. Feature Catalog

| ID | Feature | Area | Priority | Acceptance criteria (summary) |
|----|---------|------|----------|-------------------------------|
| F-01 | Transaction ingestion API | Gateway | **M** | Valid payload → 202 + `tx_id`; invalid → 422 problem+json; p95 < 150 ms |
| F-02 | Idempotent ingestion | Gateway | **M** | Duplicate `tx_id` → 409; no second investigation |
| F-03 | Sync analyze mode | Gateway | **M** | `?mode=sync` returns the final `Verdict` within the 6 s hard cap |
| F-04 | ADK investigation pipeline | Engine | **M** | All 7 stages run; session state contract honoured; per-stage timeouts |
| F-05 | Behavioral analysis | Engine | **M** | Z-score, category novelty, baseline cold-start handling |
| F-06 | Structuring / velocity detection | Engine | **M** | Smurfing scenario escalates REVIEW → BLOCK → LOCK |
| F-07 | Threat intel (Tor/VPN/ASN) | Engine | **M** | Tor exit IPs detected from cached list; VPN/hosting via ASN list |
| F-08 | Impossible travel | Engine | **M** | Dubai→London in 12 min flagged; same-city card-present exempt |
| F-09 | Device novelty | Engine | **S** | New `device_id` adds signal S10 |
| F-10 | Risk scoring + hard rules | Engine | **M** | Matches the [04 §3](./04_AGENTS_SPEC.md#3-risk-scoring-algorithm-deterministic-base) table; config-driven weights |
| F-11 | Bounded LLM adjustment | Engine | **M** | Adjustment ∈ [−10, 10]; never crosses hard-rule floor |
| F-12 | Decision policy (4 bands) | Engine | **M** | Correct band/decision per score; status mapping |
| F-13 | Early containment | Engine | **S** | H1 triggers lock before LLM stages complete |
| F-14 | Actuator: lock / block / alert | Actuator | **M** | Idempotent; audit record written; alert adapter stubbed (log + Firestore) |
| F-15 | Analyst unlock / override | Actuator + UI | **S** | Authenticated analyst can unlock; reason required; audit logged |
| F-16 | Realtime telemetry stream | Engine + Firestore | **M** | Events appear in UI < 300 ms after emission, strictly ordered by `seq` |
| F-17 | Degraded mode | Engine | **M** | LLM failure → deterministic verdict with `degraded=true` |
| F-18 | Dashboard: live transaction feed | UI | **M** | Last 50 investigations, coloured pills CLEAN / REVIEW / BLOCKED / LOCKED |
| F-19 | Dashboard: investigation terminal | UI | **M** | Auto-selects latest flagged case; typing effect; agent pills |
| F-20 | Dashboard: threat gauge | UI | **M** | SVG radial meter animates 0 → score; band colours |
| F-21 | Dashboard: account-locked banner | UI | **M** | Shown when `actuator_action.account_locked == true` |
| F-22 | Dashboard: simulation bar | UI + Gateway | **M** | 3 buttons fire scenarios via `/v1/simulations/{scenario}` |
| F-23 | Dashboard: KPI strip | UI | **S** | Total processed, fraud blocked, $ saved, avg latency, FPR (from last eval) |
| F-24 | Dashboard: agent topology view | UI | **C** | Animated graph showing which agent is active |
| F-25 | Deep review narrative (Gemini Pro) | Engine | **C** | REVIEW cases get async `deep_review` within 15 s |
| F-26 | Synthetic data generator | Simulation | **M** | 500 users, 10,000 txs, explicit schema, seeded |
| F-27 | Red-team evaluation runner | Simulation | **M** | 2,000-case balanced set; metrics report (MD + JSON + BigQuery) |
| F-28 | Baseline materialisation | Data | **M** | BigQuery → `user_baselines` → Firestore `user_profiles` sync job |
| F-29 | Intel refresh job | Data | **S** | Hourly Tor exit list refresh; cached in Firestore/GCS |
| F-30 | Auth: API key + Firebase Auth | Security | **M** (API key) / **S** (Firebase Auth) | Unauthenticated calls → 401 |
| F-31 | Health & readiness | All services | **M** | `/healthz` (liveness), `/readyz` (deps check) |
| F-32 | Model / prompt / policy version stamping | Engine | **M** | Every verdict stores `versions{}` |
| F-33 | Structured logging + tracing | All | **M** | JSON logs with `trace_id`, `tx_id`; Cloud Trace spans per stage |
| F-34 | Analyst copilot chat | UI + Engine | **W** | Future |
| F-35 | Fraud-ring graph analytics | Data | **W** | Future |

---

## 2. Functional Requirements

### 2.1 API Gateway
| ID | Requirement |
|----|-------------|
| FR-GW-01 | Validate payloads against the `Transaction` schema (amount > 0, ISO-4217 currency, ISO-3166 alpha-2 country, lat ∈ [−90,90], lon ∈ [−180,180], IPv4/IPv6). |
| FR-GW-02 | Authenticate with `X-API-Key` (Secret Manager) **or** Firebase ID token (`Authorization: Bearer`). |
| FR-GW-03 | Rate-limit per API key (default 20 req/s, burst 50). Return 429 with `Retry-After`. |
| FR-GW-04 | Create `investigations/{tx_id}` with `status=QUEUED` using a create-if-absent precondition. |
| FR-GW-05 | Publish `TxIngested` to Pub/Sub (async mode) or call the engine directly (sync mode). |
| FR-GW-06 | Expose simulation scenarios that generate realistic payload sequences with controlled timestamps. |
| FR-GW-07 | Keep the v0 alias `POST /api/analyze-tx` mapped to `POST /v1/transactions:analyze`. |

### 2.2 Agent Engine
| ID | Requirement |
|----|-------------|
| FR-AE-01 | Verify Pub/Sub push OIDC token audience and service account. |
| FR-AE-02 | Run the ADK pipeline with per-stage timeouts and a global 6 s cap. |
| FR-AE-03 | Run enrichment tools concurrently; one tool failing never fails the pipeline. |
| FR-AE-04 | Validate every LLM output against its schema; re-ask once on failure. |
| FR-AE-05 | Reject findings whose `evidence_id` is not present in `FeatureVector`. |
| FR-AE-06 | Update `user_profiles/{user_id}` (last_tx, recent_txs ring buffer, devices) **after** the verdict, in a transaction. |
| FR-AE-07 | Write the final verdict and `latency_ms` breakdown per stage. |
| FR-AE-08 | Write one row to BigQuery `investigation_results` per case (streaming insert / Storage Write API). |

### 2.3 Actuator
| ID | Requirement |
|----|-------------|
| FR-AC-01 | Accept only OIDC-authenticated calls from allowed SAs. |
| FR-AC-02 | All actions idempotent via `Idempotency-Key` header. |
| FR-AC-03 | Persist `accounts/{user_id}` lock state + append-only `accounts/{user_id}/audit/{id}`. |
| FR-AC-04 | Notifier port with adapters: `log` (default), `whatsapp` (Meta Cloud API), `sms` (future). |

### 2.4 Dashboard
| ID | Requirement |
|----|-------------|
| FR-UI-01 | Subscribe to `investigations` ordered by `started_at desc`, limit 50. |
| FR-UI-02 | Auto-select the newest case with status `ACTION_TAKEN` or band ≥ ELEVATED, unless the user pinned a case. |
| FR-UI-03 | Subscribe to `investigations/{id}/events` ordered by `seq`; render with typing effect (≤ 15 ms/char, skippable). |
| FR-UI-04 | Gauge animates over 1.2 s using an ease-out curve; colour by band. |
| FR-UI-05 | Simulation buttons disabled while a scenario is running; show toast with result. |
| FR-UI-06 | Fully keyboard-navigable; respects `prefers-reduced-motion`. |

---

## 3. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-01 | Latency | End-to-end ingest → verdict persisted (investigated case) | avg < 2.8 s, p95 < 4 s |
| NFR-02 | Latency | Fast-path clean transaction | p95 < 600 ms |
| NFR-03 | Throughput | Sustained load (demo env) | 20 tx/s without errors |
| NFR-04 | Accuracy | Balanced red-team set | > 98 % accuracy, < 1.5 % FPR, > 97 % recall |
| NFR-05 | Availability | Services (demo window) | 99.9 %; min-instances = 1 |
| NFR-06 | Explainability | Verdicts with ≥ 1 cited evidence ID | 100 % |
| NFR-07 | Auditability | Verdict stores model IDs, prompt versions, policy version, feature snapshot | 100 % |
| NFR-08 | Security | No secrets in code/images; least-privilege SAs; Firestore rules deny client writes | Mandatory |
| NFR-09 | Privacy | PII masked in logs; IP last octet masked in UI events | Mandatory |
| NFR-10 | Observability | Trace per investigation with stage spans | Mandatory |
| NFR-11 | Quality | Backend coverage ≥ 85 % (domain ≥ 95 %); frontend ≥ 70 % | CI gate |
| NFR-12 | Accessibility | WCAG 2.2 AA contrast on dashboard | Mandatory |
| NFR-13 | Portability | Full system runs locally with emulators + mock adapters | Mandatory |
| NFR-14 | Cost | Gemini tokens per investigated case | < 6k |

---

## 4. Demo User Stories

1. *As a judge,* I click **"Clean Coffee $4.50"** and see a green CLEAN pill appear within a second, with a 2-line fast-path trace.
2. *As a judge,* I click **"Smurfing Attempt"** and watch five transfers arrive. The gauge climbs from amber to orange to red, and the final transfer locks the account.
3. *As a judge,* I click **"Impossible Travel Tor Attack"**. The Threat Intel agent reports Dubai → London in 12 minutes from a Tor exit node, the account is locked **before** the orchestrator finishes writing, and a red banner shows "Account Locked · WhatsApp alert dispatched".
4. *As a fraud analyst,* I open a REVIEW case, read the Gemini Pro deep-review narrative, and click **Unlock / Approve** with a reason.
5. *As a CRO,* I see the KPI strip: processed, blocked, $ protected, avg latency, last-eval FPR.
