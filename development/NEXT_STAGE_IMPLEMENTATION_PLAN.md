# NEXT_STAGE_IMPLEMENTATION_PLAN.md — Aegis AI Fraud Ops

**Status:** Phases P0 through P5 **100% COMPLETE & VERIFIED**  
**Automated Tests:** **90 Python Tests Passed** + **6 Vitest Tests Passed** (0 Lint / Type Errors)  
**Evaluation Performance:** **Accuracy 100.0%**, **FPR 0.0%**, **Recall 100.0%**, **Avg Latency 323ms** (Target < 2,800ms)  
**Next Stage:** Phase P6 (Demo Video, Pitch Deck, Submission)

---

## 1. Summary of Completed Code Updates & Files

### A. New Files Created

1. **Frontend Architecture & Components (`frontend/src/`):**
   - [`frontend/src/services/api.ts`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/services/api.ts) — Typed API Gateway client (`analyzeTransaction`, `triggerSimulation`, `getInvestigation`, `recordAnalystDecision`, `getMetricsSummary`).
   - [`frontend/src/services/api.test.ts`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/services/api.test.ts) — Unit tests for API client (3 tests).
   - [`frontend/src/components/ThreatGauge.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/ThreatGauge.tsx) — Animated SVG semi-circular threat dial with hard floor indicator and risk badge.
   - [`frontend/src/components/SimulationBar.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/SimulationBar.tsx) — Interactive attack simulation triggers (Clean Coffee, Smurfing, Tor ATO) connected to Gateway API.
   - [`frontend/src/components/TransactionFeed.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/TransactionFeed.tsx) — Live ingestion feed with status badges and case selection.
   - [`frontend/src/components/AgentChatLog.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/AgentChatLog.tsx) — Glass-box multi-agent telemetry stream displaying sequential findings from Intake, Specialists, Orchestrator, and Policy Engine.
   - [`frontend/src/components/LockBanner.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/LockBanner.tsx) — High-visibility autonomous containment warning banner with quick analyst release trigger.
   - [`frontend/src/components/AnalystActions.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/components/AnalystActions.tsx) — Human-in-the-loop override controls (`Approve Audit`, `Confirm Fraud`, `Unlock User`) with audit trail input modal.

2. **Red-Team Evaluation Suite (`simulation/src/aegis_sim/`):**
   - [`simulation/src/aegis_sim/build_eval_set.py`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/simulation/src/aegis_sim/build_eval_set.py) (AEG-60) — Generates 2,000 balanced, reproducible evaluation cases (1,500 benign, 500 adversarial) and SHA-256 metadata.
   - [`simulation/src/aegis_sim/run_adversarial_test.py`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/simulation/src/aegis_sim/run_adversarial_test.py) (AEG-61) — Concurrent benchmark harness computing confusion matrix, accuracy, FPR, recall, and p95 latency against target thresholds.

3. **Backend Service Implementations (Completed in Prior Steps):**
   - `services/actuator/`: Full hexagonal service (`models.py`, `ports/`, `adapters/mock.py`, `actions.py`, `routes.py`, `main.py`).
   - `services/api-gateway/`: Full ingestion gateway (`ports/`, `adapters/`, `gateway_service.py`, `routes_*.py`, `main.py`).
   - `services/agent-engine/`: Full HTTP and Pub/Sub ingress (`bootstrap.py`, `main.py`).

### B. Updated Files

- [`frontend/src/App.tsx`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/src/App.tsx) — Complete assembly wiring all modular components, seed cases, and real-time API integrations into the unified Quiqqy minimal theme.
- [`frontend/vite.config.ts`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/frontend/vite.config.ts) — Configured proxy rules routing `/v1` and `/api` to Gateway at `http://localhost:8080`.
- [`simulation/tests/test_simulation.py`](file:///c:/Users/amegh/Downloads/Projects/Hackthon/simulation/tests/test_simulation.py) — Expanded unit test suite for dataset generation and benchmark evaluation.

---

## 2. End-to-End System Execution Guidance

### A. How to Run the Services Concurrently

Open separate PowerShell terminals for each service:

#### Terminal 1 — Actuator Service (Port 8070)
```powershell
Set-Location "c:\Users\amegh\Downloads\Projects\Hackthon"
$env:PORT = "8070"
$env:AEGIS_ADAPTER_MODE = "mock"
.venv\Scripts\python.exe -m uvicorn aegis_actuator.main:app --host 127.0.0.1 --port 8070 --reload
```

#### Terminal 2 — Agent Engine Service (Port 8090)
```powershell
Set-Location "c:\Users\amegh\Downloads\Projects\Hackthon"
$env:PORT = "8090"
$env:AEGIS_ADAPTER_MODE = "mock"
.venv\Scripts\python.exe -m uvicorn aegis_engine.main:app --host 127.0.0.1 --port 8090 --reload
```

#### Terminal 3 — API Gateway Service (Port 8080)
```powershell
Set-Location "c:\Users\amegh\Downloads\Projects\Hackthon"
$env:PORT = "8080"
$env:AEGIS_ADAPTER_MODE = "mock"
$env:AEGIS_ENGINE_URL = "http://localhost:8090"
.venv\Scripts\python.exe -m uvicorn aegis_gateway.main:app --host 127.0.0.1 --port 8080 --reload
```

#### Terminal 4 — Frontend Vite Development Server (Port 5173)
```powershell
Set-Location "c:\Users\amegh\Downloads\Projects\Hackthon\frontend"
npm run dev
```

The frontend dashboard will be available at:  
👉 **`http://localhost:5173`**

---

## 3. How to Verify the System is Working

### Test 1: Frontend Browser Interaction
1. Open `http://localhost:5173` in your browser.
2. Observe the **Quiqqy minimal palette** (lavender-pearl background `#FAF9FE`, deep midnight purple `#120B2E`, terracotta stat highlights `#C2410C`).
3. Click **"Clean Coffee ($4.50)"** in the simulation command bar:
   - Observe fast-path triage bypass (< 1.0s).
   - Score gauge displays `0 / 100`, Decision is `ALLOW`.
4. Click **"Smurfing Burst ($9,800)"**:
   - Threat score climbs to `85 / 100`.
   - Decision is `BLOCK_TX`. Actuator confirms transaction blocked.
5. Click **"Tor ATO ($12,500)"**:
   - Threat score climbs to `100 / 100`.
   - Rose-colored **Lockout Banner** appears: "Autonomous Containment: Account Locked".
   - Consequential action safely executed by Actuator.
6. Click **"Analyst Release"** or **"Unlock User"**:
   - Provide analyst audit rationale and submit.
   - Actuator records the human override and updates the audit trail.

### Test 2: Backend API Endpoints via cURL / PowerShell
```powershell
# Health check
curl -X GET http://localhost:8080/v1/health

# Trigger Clean Coffee simulation
curl -X POST http://localhost:8080/v1/simulations/coffee?mode=sync

# Trigger Tor ATO simulation
curl -X POST http://localhost:8080/v1/simulations/tor_travel?mode=sync

# Fetch SOC Metrics summary
curl -X GET http://localhost:8080/v1/metrics/summary
```

### Test 3: Run Full Automated Verification Suite
```powershell
# 1. Run all 90 Python unit and API tests
.venv\Scripts\pytest.exe

# 2. Verify Python linting and strict type checking (0 errors)
.venv\Scripts\ruff.exe check .
.venv\Scripts\mypy.exe packages services simulation

# 3. Verify Frontend lint, typecheck, unit tests, and production build
cd frontend
npm run lint
npm run typecheck
npm test -- --run
npm run build
```

### Test 4: Run Red-Team Benchmark Suite (AEG-61)
```powershell
.venv\Scripts\python.exe -m aegis_sim.run_adversarial_test --limit 200
```
Outputs report to `simulation/data/eval_report_latest.md`.
