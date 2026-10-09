# 08 · Data Schemas & API Contracts

| Field | Value |
|-------|-------|
| Status | ✅ Baseline v1.0 |
| Source of truth | Pydantic models in `packages/aegis-common/src/aegis_common/schemas/` → exported to `contracts/jsonschema/` |

---

## 1. Transaction Ingestion (`POST /v1/transactions:analyze`)

### 1.1 Request
```json
{
  "tx_id": "TX_982341",
  "user_id": "USR_4402",
  "timestamp": "2026-10-09T14:30:00Z",
  "amount": 7500.00,
  "currency": "USD",
  "merchant": "Global Crypto Exchange Inc",
  "merchant_category": "cryptocurrency_brokerage",
  "channel": "ECOMMERCE",
  "device_id": "DEV_AA9912",
  "ip_address": "185.220.101.5",
  "location": { "latitude": 51.5074, "longitude": -0.1278, "city": "London", "country": "GB" }
}
```

### 1.2 Validation rules
| Field | Type | Rule |
|-------|------|------|
| `tx_id` | str | `^TX_[A-Z0-9]{4,32}$`, unique |
| `user_id` | str | `^USR_[A-Z0-9]{2,32}$` |
| `timestamp` | datetime (RFC 3339, UTC) | Not more than 5 min in the future |
| `amount` | Decimal | `> 0`, `≤ 1,000,000`, 2 dp |
| `currency` | str | ISO-4217 (3 upper letters) |
| `merchant` | str | 1–120 chars, control chars stripped (**untrusted** for prompts) |
| `merchant_category` | enum | See §6 `MerchantCategory` |
| `channel` | enum | `CARD_PRESENT`, `ECOMMERCE`, `TRANSFER`, `ATM` (**new in v1**, default `ECOMMERCE`) |
| `device_id` | str | 1–64 chars |
| `ip_address` | IPvAnyAddress | Required for non-`CARD_PRESENT` |
| `location.latitude/longitude` | float | [−90, 90] / [−180, 180] |
| `location.country` | str | ISO-3166-1 alpha-2 |

### 1.3 Responses
```json
// 202 Accepted (async mode)
{ "tx_id": "TX_982341", "status": "QUEUED", "status_url": "/v1/investigations/TX_982341" }
```
```json
// 200 OK (sync mode) → Verdict
{
  "tx_id": "TX_982341", "threat_score": 100, "risk_level": "CRITICAL", "decision": "LOCK_ACCOUNT",
  "should_actuate": true, "typology": "ACCOUNT_TAKEOVER",
  "rationale": "Tor exit node + Dubai→London in 12 min (27,350 km/h) + first-ever $12.5k crypto purchase on a new device.",
  "degraded": false, "latency_ms": { "total": 2410, "enrichment": 310, "specialists": 870, "orchestrator": 760, "policy": 190 }
}
```

---

## 2. Firestore Data Model

```text
investigations/{tx_id}                       ← summary doc (UI feed + case header)
  └── events/{seq:04d}                       ← ordered telemetry (UI terminal)
user_profiles/{user_id}                      ← hot-path behavioural state (engine-only)
accounts/{user_id}                           ← simulated core-banking lock state (actuator-only)
  └── audit/{audit_id}                       ← append-only action log
system/metrics                               ← rolling KPI counters (engine closeout)
system/eval_latest                           ← last red-team summary (sim job)
intel/tor_exit_nodes                         ← cached list metadata (+ GCS object for full list)
```

### 2.1 `investigations/{tx_id}`
```json
{
  "tx_id": "TX_982341",
  "user_id": "USR_4402",
  "status": "ACTION_TAKEN",               // QUEUED | PROCESSING | COMPLETED | ACTION_TAKEN | FAILED
  "tx": { "amount": 12500.0, "currency": "USD", "merchant": "Global Crypto Exchange Inc",
          "merchant_category": "cryptocurrency_brokerage", "city": "London", "country": "GB",
          "channel": "ECOMMERCE" },
  "threat_score": 100,
  "risk_level": "CRITICAL",               // LOW | ELEVATED | HIGH | CRITICAL
  "decision": "LOCK_ACCOUNT",             // ALLOW | REVIEW | BLOCK_TX | LOCK_ACCOUNT | DECLINE_LOCKED
  "should_actuate": true,
  "typology": "ACCOUNT_TAKEOVER",
  "rationale": "…",
  "cited_evidence": ["ip.is_tor", "travel.speed_kmh", "monetary.z_score", "device.is_new"],
  "score_breakdown": { "base": 100, "floor": 90, "llm_adjustment": 0,
                       "signals": { "S1_monetary": 25, "S6_anon_network": 30, "S8_travel": 35 },
                       "rules": ["H1"] },
  "features_snapshot": { "...": "FeatureVector (PII-reduced)" },
  "actuator_action": { "account_locked": true, "tx_blocked": true, "alert_dispatched": true,
                       "dispatch_channel": "WHATSAPP_REST", "early_containment": true },
  "deep_review": null,                    // CaseNarrative when available
  "analyst_decision": null,               // { action, reason, analyst_uid, at }
  "degraded": false,
  "versions": { "policy": "1.0.0",
                "orchestrator": { "model": "gemini-…-flash", "prompt": "1.0.0" },
                "specialist":   { "model": "gemini-…-flash-lite", "prompt": "1.0.0" } },
  "latency_ms": { "total": 2410, "enrichment": 310, "specialists": 870, "orchestrator": 760, "policy": 190 },
  "event_count": 11,
  "started_at": 1791556200000,
  "completed_at": 1791556202410
}
```

### 2.2 `investigations/{tx_id}/events/{seq}`
```json
{ "seq": 6, "agent": "Threat Intel", "action": "TOOL_RESULT", "severity": "CRITICAL",
  "message": "Tor exit node · Dubai→London 5,470 km in 12 min (27,350 km/h)",
  "data": { "is_tor": true, "speed_kmh": 27350, "distance_km": 5470, "elapsed_min": 12 },
  "latency_ms": 18, "timestamp": 1791556200840 }
```

### 2.3 `user_profiles/{user_id}`
```json
{
  "user_id": "USR_4402",
  "home_city": "Dubai", "home_country": "AE",
  "baseline": { "avg_amount": 74.1, "std_amount": 19.8, "median_amount": 71.0, "p95_amount": 109.5,
                "tx_count_90d": 61, "known_categories": ["coffee_shop", "grocery", "fuel", "restaurant"],
                "known_countries": ["AE", "OM"], "as_of": "2026-10-09", "source": "bq_user_baselines" },
  "known_devices": ["DEV_11AB02", "DEV_77CD10"],
  "last_tx": { "tx_id": "TX_982300", "ts": 1791555480000, "lat": 25.2048, "lon": 55.2708,
               "city": "Dubai", "country": "AE", "channel": "CARD_PRESENT" },
  "recent_txs": [ { "ts": 1791555480000, "amount": 42.0, "category": "restaurant" } ],   // ring buffer ≤ 50
  "updated_at": 1791555480100
}
```

### 2.4 `accounts/{user_id}`
```json
{ "user_id": "USR_4402", "locked": true, "locked_at": 1791556201100,
  "lock_reason": "Aegis CRITICAL: ACCOUNT_TAKEOVER (case TX_982341)", "locked_by": "sa-agent-engine",
  "unlock_history": [] }
```

### 2.5 Indexes (`firestore.indexes.json`)
| Collection | Fields | Purpose |
|------------|--------|---------|
| `investigations` | `started_at DESC` | Feed |
| `investigations` | `status ASC, started_at DESC` | Filter by status |
| `investigations` | `risk_level ASC, started_at DESC` | Auto-select flagged cases |
| `events` (collection group) | `seq ASC` | Terminal order (single-field, automatic) |

### 2.6 Security rules (summary — full file in [12](./12_SECURITY_COMPLIANCE.md))
- `investigations/**`: read if authenticated with claim `role in ['analyst','viewer']`; **no client writes**.
- `user_profiles`, `accounts`, `intel`, `system/*` except `metrics`/`eval_latest`: **deny all clients**.

---

## 3. BigQuery — dataset `fraud_telemetry` (location `US`)

### 3.1 `historical_txs` (partitioned by `DATE(ts)`, clustered by `user_id, merchant_category`)
```json
[
  {"name": "tx_id",             "type": "STRING",    "mode": "REQUIRED"},
  {"name": "user_id",           "type": "STRING",    "mode": "REQUIRED"},
  {"name": "ts",                "type": "TIMESTAMP", "mode": "REQUIRED"},
  {"name": "amount",            "type": "NUMERIC",   "mode": "REQUIRED"},
  {"name": "currency",          "type": "STRING",    "mode": "REQUIRED"},
  {"name": "merchant",          "type": "STRING",    "mode": "NULLABLE"},
  {"name": "merchant_category", "type": "STRING",    "mode": "REQUIRED"},
  {"name": "channel",           "type": "STRING",    "mode": "REQUIRED"},
  {"name": "device_id",         "type": "STRING",    "mode": "NULLABLE"},
  {"name": "ip_address",        "type": "STRING",    "mode": "NULLABLE"},
  {"name": "latitude",          "type": "FLOAT64",   "mode": "NULLABLE"},
  {"name": "longitude",         "type": "FLOAT64",   "mode": "NULLABLE"},
  {"name": "city",              "type": "STRING",    "mode": "NULLABLE"},
  {"name": "country",           "type": "STRING",    "mode": "NULLABLE"},
  {"name": "is_fraud",          "type": "BOOL",      "mode": "REQUIRED"},
  {"name": "fraud_type",        "type": "STRING",    "mode": "NULLABLE"}
]
```
Saved as `simulation/bq_schema.json`. Load with an explicit schema (no `--autodetect`):
```bash
bq load --source_format=CSV --skip_leading_rows=1 \
  --time_partitioning_field=ts --clustering_fields=user_id,merchant_category \
  fraud_telemetry.historical_txs data/historical_txs.csv simulation/bq_schema.json
```

### 3.2 `user_baselines` (materialised nightly by scheduled query)
```sql
CREATE OR REPLACE TABLE `${PROJECT}.fraud_telemetry.user_baselines` AS
SELECT
  user_id,
  AVG(amount)                                   AS avg_amount,
  STDDEV_SAMP(amount)                           AS std_amount,
  APPROX_QUANTILES(amount, 100)[OFFSET(50)]     AS median_amount,
  APPROX_QUANTILES(amount, 100)[OFFSET(95)]     AS p95_amount,
  COUNT(*)                                      AS tx_count_90d,
  ARRAY_AGG(DISTINCT merchant_category)         AS known_categories,
  ARRAY_AGG(DISTINCT country IGNORE NULLS)      AS known_countries,
  ARRAY_AGG(DISTINCT device_id IGNORE NULLS)    AS known_devices,
  APPROX_TOP_COUNT(city, 1)[OFFSET(0)].value    AS home_city,
  APPROX_TOP_COUNT(country, 1)[OFFSET(0)].value AS home_country,
  CURRENT_DATE()                                AS as_of
FROM `${PROJECT}.fraud_telemetry.historical_txs`
WHERE is_fraud = FALSE
  AND ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
GROUP BY user_id;
```

### 3.3 Hot-path fallback query (cache miss only)
```sql
SELECT AVG(amount) AS avg_amount, STDDEV_SAMP(amount) AS std_amount, COUNT(*) AS tx_count,
       ARRAY_AGG(DISTINCT merchant_category) AS known_categories
FROM `${PROJECT}.fraud_telemetry.historical_txs`
WHERE user_id = @user_id AND is_fraud = FALSE
  AND ts >= TIMESTAMP_SUB(@as_of, INTERVAL 90 DAY)
```

### 3.4 `investigation_results` (one row per verdict, partitioned by `DATE(completed_at)`)
`tx_id, user_id, completed_at, amount, merchant_category, threat_score, risk_level, decision, typology, degraded, llm_adjustment, signals JSON, rules ARRAY<STRING>, latency_total_ms, model_orchestrator, model_specialist, prompt_versions JSON, policy_version, eval_run_id (nullable), label_is_fraud (nullable)`

### 3.5 `eval_runs`
`run_id, started_at, dataset_version, n_cases, accuracy, precision, recall, f1, fpr, review_rate, latency_avg_ms, latency_p50_ms, latency_p95_ms, tokens_avg, git_sha, config JSON`

---

## 4. Pub/Sub

| Topic | Subscription | Type | Settings |
|-------|--------------|------|----------|
| `tx-ingest` | `tx-ingest-engine-push` | Push → `agent-engine /internal/pubsub/tx-ingested` (OIDC `sa-pubsub-invoker`) | ack deadline 30 s, retry 1 s–60 s exponential, max delivery 5 |
| `tx-ingest-dlq` | `tx-ingest-dlq-pull` | Pull | retention 7 d |

**Message (`TxIngested` v1)**: `data` = JSON `Transaction`; attributes `{ "schema": "tx_ingested.v1", "tx_id": "...", "trace_id": "...", "source": "simulator|api" }`.

---

## 5. Domain Models (Pydantic, abbreviated)

```python
class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    city: str = Field(max_length=80)
    country: str = Field(pattern=r"^[A-Z]{2}$")


class Transaction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    tx_id: str = Field(pattern=r"^TX_[A-Z0-9]{4,32}$")
    user_id: str = Field(pattern=r"^USR_[A-Z0-9]{2,32}$")
    timestamp: AwareDatetime
    amount: Decimal = Field(gt=0, le=1_000_000, decimal_places=2)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    merchant: str = Field(min_length=1, max_length=120)
    merchant_category: MerchantCategory
    channel: Channel = Channel.ECOMMERCE
    device_id: str = Field(min_length=1, max_length=64)
    ip_address: IPvAnyAddress | None = None
    location: Location


class FeatureVector(BaseModel):
    baseline: UserBaseline  # avg, std, count, cold_start
    monetary: MonetaryAnomaly  # z_score, ratio_to_p95
    category: CategoryCheck  # is_novel, is_high_risk
    velocity: VelocityStats  # count_60s, count_15m, near_threshold_count_15m, in_structuring_band, structuring_hit
    ip: IpReputation  # is_tor, is_vpn, is_hosting, asn, asn_type, abuse_score, country, unknown
    travel: TravelCheck  # prev_city, distance_km, elapsed_min, speed_kmh, impossible, exempt
    device: DeviceCheck  # is_new
    geo: GeoCheck  # country_mismatch
```

---

## 6. Enumerations

| Enum | Values |
|------|--------|
| `InvestigationStatus` | `QUEUED`, `PROCESSING`, `COMPLETED`, `ACTION_TAKEN`, `FAILED` |
| `RiskLevel` | `LOW`, `ELEVATED`, `HIGH`, `CRITICAL` |
| `Decision` | `ALLOW`, `REVIEW`, `BLOCK_TX`, `LOCK_ACCOUNT`, `DECLINE_LOCKED` |
| `Typology` | `NONE`, `ACCOUNT_TAKEOVER`, `STRUCTURING`, `CREDENTIAL_STUFFING`, `CARD_TESTING`, `MERCHANT_DEVIATION`, `OTHER` |
| `AgentName` | `Orchestrator`, `Behavioral Analyst`, `Threat Intel`, `Policy Engine`, `Actuator`, `Deep Review` |
| `TelemetryAction` | `THOUGHT`, `TOOL_CALL`, `TOOL_RESULT`, `FINDING`, `VERDICT`, `ACTION`, `ERROR` |
| `Channel` | `CARD_PRESENT`, `ECOMMERCE`, `TRANSFER`, `ATM` |
| `MerchantCategory` | `coffee_shop`, `grocery`, `restaurant`, `fuel`, `retail`, `electronics`, `travel`, `utilities`, `pharmacy`, `entertainment`, `cryptocurrency_brokerage`*, `gambling`*, `money_transfer`*, `gift_cards`*, `wire_transfer`* (* = high-risk) |
| `DispatchChannel` | `WHATSAPP_REST`, `SMS`, `EMAIL`, `PUSH`, `LOG_ONLY` |

---

## 7. UI Status Pill Mapping

| `status` | `decision` | Pill |
|----------|-----------|------|
| `QUEUED` / `PROCESSING` | — | `PROCESSING` (shimmer) |
| `COMPLETED` | `ALLOW` | `CLEAN` 🟢 |
| `COMPLETED` | `REVIEW` | `REVIEW` 🟡 |
| `ACTION_TAKEN` | `BLOCK_TX` | `BLOCKED` 🟠 |
| `ACTION_TAKEN` | `LOCK_ACCOUNT` / `DECLINE_LOCKED` | `LOCKED` 🔴 |
| `FAILED` | — | `ERROR` ⚪ |
