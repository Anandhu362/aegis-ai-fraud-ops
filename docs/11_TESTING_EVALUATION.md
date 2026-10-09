# 11 · Testing & Evaluation Strategy

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Related | [04_AGENTS_SPEC](./04_AGENTS_SPEC.md) · [05_FEATURES_REQUIREMENTS](./05_FEATURES_REQUIREMENTS.md) |

---

## 1. Test Pyramid

| Layer | Scope | Tools | Runs | Gate |
|-------|-------|-------|------|------|
| **Unit** | Domain (scoring, policy, geo, velocity), settings, mappers, React components/hooks | pytest, hypothesis, Vitest, RTL | Every PR | Coverage ≥ 85 % (domain ≥ 95 %) |
| **Contract** | Pydantic ↔ JSON Schema ↔ TS types; API request/response shapes; Pub/Sub message | pytest, schemathesis (OpenAPI fuzz) | Every PR | Zero drift |
| **Golden prompt** | Each LLM agent vs. curated cases (≥ 20 each) | pytest + mock LLM / real Gemini (nightly) | PR (mock), nightly (real) | 100 % schema-valid, ≥ 95 % expected labels |
| **Integration** | Adapters vs. Firestore emulator; BigQuery sandbox; actuator HTTP | pytest, emulators | PR (emulator), nightly (BigQuery) | Pass |
| **Agent eval** | Full ADK pipeline trajectories | `adk eval` / pytest harness | Nightly | Trajectory + final-response match |
| **E2E** | Dashboard flows (3 simulation buttons, lock banner, analyst unlock) | Playwright | Pre-deploy | Pass |
| **Load** | 20 tx/s sustained, 50 tx/s burst | Locust or k6 | Before demo freeze | p95 < 4 s, 0 % errors |
| **Red-team eval** | 2,000-case balanced benchmark | `simulation/run_adversarial_test.py` | Nightly + before demo | Accuracy > 98 %, FPR < 1.5 %, avg latency < 2.8 s |

---

## 2. Critical Unit Test Cases (domain)

| Area | Case |
|------|------|
| Scoring | Each signal S1–S10 fires at exact threshold boundaries (z = 2.0, 3.0, 4.0; speed = 500, 800) |
| Scoring | Tor and VPN not additive (max 30) |
| Scoring | Base score capped at 100 |
| Hard rules | H1 floor = 90 when Tor ∧ impossible travel; H2 floor = 72 on structuring hit |
| LLM adjustment | Clamped to ±10; never below floor; never > 100 or < 0 |
| Policy | Bands at 30/31, 70/71, 85/86 boundaries |
| Geo | Haversine Dubai→London ≈ 5,470 km (±1 %); Δt = 0 guarded |
| Travel | Same-city card-present exemption (< 50 km) |
| Velocity | Structuring needs ≥ 2 prior in band within 15 min **and** current in band |
| Baseline | Cold-start uses population prior + `cold_start=true`; std floor applied |
| Property tests | Hypothesis: score ∈ [0,100] for any feature vector; monotonic (adding a signal never lowers score) |

---

## 3. Evaluation Dataset Design

v0 used 500 adversarial-only cases, which makes FPR impossible to compute. v1 uses a **balanced, labelled, versioned** set.

| Segment | Count | Label | Description |
|---------|-------|-------|-------------|
| Benign — routine | 1,100 | 0 | Home-city purchases drawn from the user's baseline distribution |
| Benign — hard negatives | 400 | 0 | Legit travel with gradual timestamps; corporate/hotel VPN with known device; large but in-category purchase (≤ p99); new merchant in a known category; first card-present abroad after a flight-plausible gap |
| Adversarial — Structuring / smurfing | 150 | 1 | Bursts of 3–10 txs at $9,500–$9,990 within 60 s–15 min |
| Adversarial — Impossible travel ATO | 150 | 1 | Card-present in home city → e-commerce abroad 5–30 min later, often Tor/VPN, new device |
| Adversarial — Credential stuffing spike | 150 | 1 | Tor/hosting ASN IPs, random high amounts, high-risk categories |
| Adversarial — Merchant deviation | 50 | 1 | First-ever high-risk category, z ≥ 4, new device |
| **Total** | **2,000** | | Seed `20261009`; stored as `simulation/data/eval_set_v1.jsonl` + metadata hash |

**Label semantics:** predicted positive ⇔ decision ∈ {BLOCK_TX, LOCK_ACCOUNT}. For multi-tx sequences (smurfing), the **sequence** is a true positive if any tx in it reaches BLOCK/LOCK by the 3rd in-band tx. Benign txs inside a sequence are scored individually.

---

## 4. Metrics (definitions)

| Metric | Formula | Target |
|--------|---------|--------|
| Accuracy | (TP + TN) / N | > 98 % |
| Precision | TP / (TP + FP) | > 95 % |
| Recall (TPR) | TP / (TP + FN) | > 97 % |
| F1 | 2·P·R / (P + R) | > 96 % |
| **False Positive Rate** | FP / (FP + TN) | **< 1.5 %** |
| Review rate | count(REVIEW) / N | < 5 % (informational) |
| Latency avg / p50 / p95 | Gateway receipt → verdict persisted (`completed_at − received_at`) | avg < 2.8 s, p95 < 4 s |
| Degraded rate | count(degraded) / N | < 1 % |
| Tokens / investigated case | Sum of usage metadata | < 6k |
| Per-typology recall | Recall per adversarial segment | each > 95 % |

**Latency measurement:** the runner uses `?mode=sync` with concurrency 10 (configurable), records client wall time, and also reads the server `latency_ms.total` so network overhead can be shown separately.

---

## 5. Red-Team Runner (`run_adversarial_test.py`) Behaviour

```text
1. Load eval_set_v1.jsonl (or --generate with seed).
2. Pre-seed user_profiles for eval users (baseline + last_tx for travel cases).
3. Fire requests concurrently (httpx.AsyncClient, semaphore = --concurrency), preserving the
   intra-sequence order and timestamps for smurfing/travel sequences.
4. Collect verdicts + latencies; compute metrics + confusion matrix + per-typology table.
5. Emit: reports/eval_<run_id>.md, reports/eval_<run_id>.json, BigQuery eval_runs row,
   Firestore system/eval_latest (for the dashboard KPI strip).
6. Exit code 1 if any target is missed (used by nightly CI).
```

**Report template (excerpt)**
```text
Aegis Red-Team Evaluation — run 2026-10-09T02:00Z (git 3f2a1c9, dataset v1, policy 1.0.0)
Cases: 2000 (1500 benign / 500 adversarial)    Concurrency: 10    Models: <flash> / <flash-lite>
┌──────────────┬─────────┬────────┐
│ Metric       │ Value   │ Target │
├──────────────┼─────────┼────────┤
│ Accuracy     │ 98.9 %  │ >98 %  │
│ FPR          │ 0.9 %   │ <1.5 % │
│ Recall       │ 98.4 %  │ >97 %  │
│ Avg latency  │ 2.31 s  │ <2.8 s │
│ p95 latency  │ 3.42 s  │ <4.0 s │
└──────────────┴─────────┴────────┘
```
*(Numbers are illustrative placeholders. Only publish real measured results.)*

---

## 6. Mocking & Determinism

| Dependency | Mock strategy |
|-----------|---------------|
| Gemini | `MockLlm` adapter returns schema-valid reports derived deterministically from features (rule mirror) |
| Firestore | Emulator (integration) / in-memory dict store (unit) |
| BigQuery | In-memory baseline fixtures; real BigQuery only in nightly integration |
| OSINT | Static Tor/ASN fixture lists (includes `185.220.101.0/24` as Tor sample range for demos) |
| Actuator | `respx` mocked HTTP in engine tests; in-memory ledger in actuator tests |
| Time | `freezegun` / injected `Clock` port |

---

## 7. Definition of "Demo-Ready"

- [ ] All three simulation buttons produce the expected decisions 10/10 times in `demo`.
- [ ] The latest red-team run meets all targets and is shown in the KPI strip.
- [ ] p95 latency < 4 s under 20 tx/s for 5 min.
- [ ] Playwright E2E green against `demo`.
- [ ] Degraded mode tested by forcing an LLM timeout (`AEGIS_TIMEOUT_LLM_MS=1`). The UI shows a degraded badge and critical cases still lock.
