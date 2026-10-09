# 12 · Security, Privacy & Compliance

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Related | [10_DEVOPS_AUTOMATION §6](./10_DEVOPS_AUTOMATION.md#6-iam--service-accounts--roles-least-privilege) |

---

## 1. Threat Model (STRIDE-lite)

| Threat | Asset / Entry point | Mitigation |
|--------|---------------------|------------|
| **Spoofing:** unauthenticated callers spam the API and burn Gemini credits | api-gateway | API key (Secret Manager, hashed compare) or Firebase ID token; App Check for dashboard; per-key rate limit; Cloud Armor (v2) |
| **Spoofing:** fake Pub/Sub pushes to the engine | agent-engine | Verify OIDC token (audience + `sa-pubsub-invoker` email); `--no-allow-unauthenticated` |
| **Tampering:** client writes to Firestore to fake verdicts | Firestore | Security rules deny all client writes |
| **Tampering:** prompt injection via `merchant` / free-text fields | LLM agents | Sanitise + length-cap; wrap in `<transaction_data>` with an "untrusted data" instruction; structured output; LLM cannot trigger actions; adjustment bounded ±10 |
| **Repudiation:** disputed account locks | actuator | Append-only `accounts/{uid}/audit`, verdict snapshot with model/prompt/policy versions, Cloud Audit Logs |
| **Information disclosure:** PII in logs/UI/LLM | logs, Firestore, Vertex | PII masking processor; IP last-octet masked in UI events; pseudonymous IDs; data minimisation in prompts; Vertex AI does not train on customer data |
| **Denial of service:** burst traffic | gateway/engine | Rate limit, Cloud Run max-instances, Pub/Sub buffering, DLQ |
| **Elevation of privilege:** compromised engine abuses banking actions | actuator | Isolated service, internal ingress, IAM invoker restricted, narrow API, idempotency + audit |

---

## 2. Authentication & Authorisation

| Caller → Target | Mechanism |
|-----------------|-----------|
| Simulator / external client → gateway | `X-API-Key` (per-client key, stored as SHA-256 hash in Secret Manager JSON) |
| Dashboard → gateway | Firebase Auth ID token (`Authorization: Bearer`) + App Check token; custom claim `role` ∈ {`viewer`, `analyst`, `admin`} |
| Dashboard → Firestore | Firebase Auth + security rules (read-only) |
| Pub/Sub → engine | OIDC token from `sa-pubsub-invoker`, audience = engine URL |
| Gateway / engine → actuator | Google-signed ID token (service-to-service), IAM `run.invoker` |
| Engine → Vertex AI / BigQuery / Firestore | ADC via runtime service account |
| CI → GCP | Workload Identity Federation (no long-lived keys) |

**Analyst actions** (unlock / override) require `role in ['analyst','admin']`. The gateway passes the analyst UID and reason to the actuator, and the audit entry records both.

---

## 3. Firestore Security Rules

```javascript
// frontend/firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    function signedIn() { return request.auth != null; }
    function hasRole(roles) { return signedIn() && request.auth.token.role in roles; }

    // Investigations + telemetry: read-only for analysts/viewers. All writes are server-side (Admin SDK).
    match /investigations/{txId} {
      allow read: if hasRole(['viewer', 'analyst', 'admin']);
      allow write: if false;
      match /events/{eventId} {
        allow read: if hasRole(['viewer', 'analyst', 'admin']);
        allow write: if false;
      }
    }

    // Public KPI docs for the dashboard
    match /system/{docId} {
      allow read: if hasRole(['viewer', 'analyst', 'admin']) && docId in ['metrics', 'eval_latest'];
      allow write: if false;
    }

    // Everything else (user_profiles, accounts, intel): server-only
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

> [!TIP]
> For a frictionless judge demo, give the dashboard an **anonymous Firebase Auth** sign-in plus a Cloud Function / Admin script that assigns `role=viewer` to anonymous users. Analyst actions then still need a real login.

---

## 4. Secrets Management

| Secret | Store | Consumer | Rotation |
|--------|-------|----------|----------|
| API keys (hashed) | Secret Manager `aegis-api-keys` | gateway | On demand; runbook `rotate-api-key.md` |
| WhatsApp Cloud API token | `aegis-whatsapp-token` | actuator | 60 days |
| OSINT provider key (optional) | `aegis-osint-key` | intel-refresh job | 90 days |
| Firebase web config | Not secret (public by design) | frontend | — |

Rules: no secrets in Git, `.env`, Docker images, or CI logs. `gitleaks` runs in pre-commit and CI. Mount secrets with `--set-secrets` (env or volume).

---

## 5. Privacy & Data Handling

| Principle | Implementation |
|-----------|----------------|
| Data minimisation | LLM prompts receive **features**, not raw history; no names, emails, phone numbers, or PANs anywhere in the system |
| Pseudonymisation | `user_id` values are synthetic/pseudonymous; production would use a keyed hash (HMAC) |
| No card data | No PAN/CVV/track data is ingested. This keeps the system outside the PCI DSS cardholder-data scope in the demo |
| Masking | Logs: IPv4 last octet → `x`, emails/phones/16-digit numbers redacted. UI telemetry: masked IP |
| Retention | Firestore TTL 30 days on investigations (demo); BigQuery partition expiration 400 days (configurable) |
| Residency | Single-region deployment; production pinned to the customer's jurisdiction |
| Synthetic data only | All hackathon data is Faker-generated. No real customer data |

---

## 6. LLM / AI Safety Controls

| Control | Detail |
|---------|--------|
| Structured output only | No free-form text paths into actions |
| Bounded influence | LLM can shift the score by ±10 at most; it cannot cross hard-rule floors and cannot call actuator tools |
| Evidence validation | Findings must cite existing `evidence_id`s; otherwise they are dropped and logged |
| Injection hardening | Untrusted fields are delimited and length-capped; a regex strips instruction-like patterns (`ignore previous`, `system:`) from merchant names before prompting, and logs them as a signal |
| Fallback | Deterministic verdict if the LLM is unavailable or invalid |
| Versioning | Model ID + prompt version + policy version stored on every verdict |
| Human-in-the-loop | REVIEW band → analyst queue; analysts can unlock/override with an audited reason |
| Fairness | No protected attributes (gender, nationality, religion, age) are used as features; country is used only for travel/geo-mismatch logic |

---

## 7. Compliance Mapping (talking points for the pitch)

| Framework | Relevance | How Aegis aligns |
|-----------|-----------|------------------|
| **PCI DSS v4.0** | Card data security | No PAN storage; network segmentation via Cloud Run ingress; least privilege; audit logs |
| **GDPR / UAE PDPL** | Personal data (IP, location) | Minimisation, purpose limitation, retention TTL, residency option, explainable decisions (Art. 22-style meaningful information) |
| **AML / CTR structuring rules** | Structuring under reporting thresholds | Dedicated structuring detector; configurable threshold per jurisdiction |
| **Model Risk Management (e.g. SR 11-7 style)** | Governance of models | Versioned prompts/policy, golden tests, nightly eval, documented limitations, human override |
| **EU AI Act** (credit/fraud-adjacent systems) | Transparency, human oversight, logging | Telemetry trail, human-in-loop band, record-keeping |
| **PSD2 SCA** | Step-up authentication | REVIEW band triggers simulated step-up auth |

> [!NOTE]
> These mappings are design-intent talking points, not certifications.

---

## 8. Security Checklist (pre-demo)

- [ ] No service except the gateway allows unauthenticated invocation.
- [ ] Actuator ingress = internal; invoker bindings verified.
- [ ] Firestore rules deployed; Rules Playground tests pass (client write → denied).
- [ ] API key rotated after the video recording.
- [ ] Budget alerts configured.
- [ ] `gitleaks`, `pip-audit`, `npm audit --omit=dev`, Trivy image scan: no high/critical findings.
- [ ] Containers run as non-root; base images pinned by digest.
