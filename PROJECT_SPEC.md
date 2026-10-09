# Project Specification: Aegis AI Fraud Ops (BFSI Multi-Agent Defense)

**Target Hackathon:** Google Cloud AI Builder Cup 2026  
**Track:** BFSI (Intelligent Risk, Fraud & Financial Experiences)  
**Deployment Target:** Google Cloud Run (Backend Microservices) + Firebase Hosting (Web Dashboard)  
**Core Technologies:** Google Vertex AI (Gemini Pro, Gemini Flash), Google Cloud BigQuery, Cloud Firestore, FastAPI, React 18, Vite, Tailwind CSS.

---

## 1. System Architecture & Component Mapping

                              [ Incoming Transaction Stream ]
                                             │
                                             ▼
                                 [ FastAPI Gateway ] (Cloud Run)
                                             │
                                             ▼
                         ┌──────────────────────────────────────┐
                         │    Orchestrator Agent (Gemini Pro)   │
                         │  - Evaluates initial anomaly         │
                         │  - Delegates tasks asynchronously    │
                         │  - Streams thoughts to Firestore     │
                         └──────────────┬───────────────────────┘
                                        │
                ┌───────────────────────┴───────────────────────┐
                ▼                                               ▼
 ┌─────────────────────────────┐                 ┌─────────────────────────────┐
 │  Behavioral Analyst Agent   │                 │   Threat Intel Agent        │
 │      (Gemini Flash)         │                 │      (Gemini Flash)         │
 │  - bq_client Tool           │                 │  - osint_client Tool        │
 │  - Historical Z-Score stats │                 │  - IP/GEO/VPN Verification  │
 └──────────────┬──────────────┘                 └──────────────┬──────────────┘
                │                                               │
                └───────────────────────┬───────────────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────────────┐
                         │       Synthesis & Verdict Engine     │
                         │     Calculates Final Threat Score    │
                         └──────────────┬───────────────────────┘
                                        │
                     ┌──────────────────┴──────────────────┐
                     │                                     │
       [ Threat Score > 85 ]                 [ Sync to Realtime DB ]
                     │                                     │
                     ▼                                     ▼
         ┌───────────────────────┐             ┌───────────────────────┐
         │    Actuator Tool      │             │  Cloud Firestore Log  │
         │ - Locks User Account  │             └───────────┬───────────┘
         │ - Dispatches Alert    │                         │
         └───────────────────────┘                         ▼
                                               ┌───────────────────────┐
                                               │ React UI (Firebase)   │
                                               │ Live Agent Telemetry  │
                                               └───────────────────────┘

---

## 2. Monorepo Directory Layout

```text
aegis-ai-fraud-ops/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py        # Master logic (Gemini Pro)
│   │   ├── behavioral.py          # BigQuery statistical analyst (Gemini Flash)
│   │   └── threat_intel.py        # Network & OSINT verification (Gemini Flash)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── bq_client.py           # BigQuery historical lookup tool
│   │   ├── osint_client.py        # IP geolocation & VPN lookup tool
│   │   └── actuator.py            # Account freeze and alert dispatcher
│   ├── config.py                  # GCP settings, Vertex AI init, environment vars
│   ├── main.py                    # FastAPI routes & Firestore streaming
│   ├── Dockerfile                 # Container image for Cloud Run
│   └── requirements.txt           # Python backend dependencies
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx         # Enterprise status bar & branding
│   │   │   ├── TransactionFeed.tsx# Live transaction incoming stream
│   │   │   ├── InvestigationView.tsx # Active reasoning view
│   │   │   ├── AgentChatLog.tsx   # Live agent dialogue & thoughts
│   │   │   └── ThreatGauge.tsx    # Visual SVG/Canvas risk meter
│   │   ├── services/
│   │   │   ├── firebase.ts        # Firestore client init
│   │   │   └── api.ts             # Cloud Run REST client
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css              # Tailwind CSS directives
│   ├── package.json
│   ├── vite.config.ts
│   └── firebase.json              # Firebase Hosting deployment config
├── simulation/
│   ├── bq_schema.json             # Historical BigQuery table definitions
│   ├── generate_sims.py           # Synthetic dataset generator (Faker/Pandas)
│   └── run_adversarial_test.py    # Test runner for evaluation metrics
└── README.md
```

---

## 3. Data Schemas & API Contracts

### 3.1 Transaction Ingestion Payload (POST /api/analyze-tx)
```json
{
  "tx_id": "TX_982341",
  "user_id": "USR_4402",
  "timestamp": "2026-10-09T14:30:00Z",
  "amount": 7500.00,
  "currency": "USD",
  "merchant": "Global Crypto Exchange Inc",
  "merchant_category": "cryptocurrency_brokerage",
  "device_id": "DEV_AA9912",
  "ip_address": "185.220.101.5",
  "location": {
    "latitude": 51.5074,
    "longitude": -0.1278,
    "city": "London",
    "country": "GB"
  }
}
```

### 3.2 Firestore Realtime Investigation Document (investigations/{tx_id})
```json
{
  "tx_id": "TX_982341",
  "user_id": "USR_4402",
  "status": "PROCESSING",
  "threat_score": 92,
  "started_at": 1728484200000,
  "completed_at": 1728484204500,
  "telemetry": [
    {
      "step": 1,
      "agent": "Orchestrator",
      "action": "THOUGHT",
      "message": "High-value crypto purchase flagged ($7500.00). Initiating behavioral & threat verification.",
      "timestamp": 1728484200500
    },
    {
      "step": 2,
      "agent": "Behavioral Analyst",
      "action": "TOOL_CALL",
      "message": "Querying BigQuery for USR_4402 90-day moving average.",
      "timestamp": 1728484201200
    },
    {
      "step": 3,
      "agent": "Threat Intel",
      "action": "TOOL_CALL",
      "message": "Checking IP 185.220.101.5 against threat databases.",
      "timestamp": 1728484201800
    },
    {
      "step": 4,
      "agent": "Orchestrator",
      "action": "VERDICT",
      "message": "Critical risk confirmed: Z-score +4.8 above normal; IP resolved to a known Tor exit node with impossible travel from Dubai swipe 15m ago.",
      "timestamp": 1728484203900
    }
  ],
  "actuator_action": {
    "account_locked": true,
    "alert_dispatched": true,
    "dispatch_channel": "WHATSAPP_REST"
  }
}
```

---

## 4. Agent Prompts & Functional Logic

### Agent 1: Orchestrator (backend/agents/orchestrator.py)
Model: gemini-1.5-pro (or gemini-2.5-flash with temperature 0.1)

System Prompt:
```text
You are the Chief Fraud Orchestration Agent for an enterprise tier-1 bank.
Your job is to coordinate specialized investigative agents (Behavioral Analyst and Threat Intelligence)
to assess financial transaction risk.

Rules:
1. Never guess facts. Always rely on reports returned by your sub-agents.
2. Delegate checks in parallel whenever possible.
3. Compute a final normalized Threat Score between 0 and 100 based on evidence:
   - 0-30: Normal / Expected variation
   - 31-70: Elevated Risk / Requires Human Analyst Review
   - 71-100: Critical Compromise / High-probability fraud
4. Emit your thoughts and progress clearly in structured steps.
5. Return the final decision as a strict JSON object containing:
   threat_score (int), risk_level (str), rationale (str), and should_actuate (bool).
```

### Agent 2: Behavioral Analyst (backend/agents/behavioral.py)
Model: gemini-1.5-flash

System Prompt:
```text
You are a Quantitative Behavioral Fraud Analyst.
You receive a transaction and query historical account telemetry using the `query_historical_stats` tool.

Logic:
1. Extract user_id and amount.
2. Execute tool query for past 90 days average and standard deviation.
3. Calculate the standard score (Z-Score): Z = (amount - avg_amount) / std_dev.
4. If Z > 3.0, mark as high monetary anomaly.
5. Check category match (has user ever transacted with this merchant type?).
6. Return a concise JSON summary: { z_score: float, category_deviation: bool, summary: str }.
```

### Agent 3: Threat Intelligence (backend/agents/threat_intel.py)
Model: gemini-1.5-flash

System Prompt:
```text
You are a Cyber Threat Intelligence Specialist in banking telemetry.
You analyze incoming IP, device fingerprints, and geolocation coordinates.

Logic:
1. Invoke `lookup_ip_reputation(ip_address)` to check Tor nodes, commercial VPN proxies, and ASN reputation.
2. Invoke `verify_velocity_travel(user_id, current_location, timestamp)` to test for impossible travel velocity (>800 km/h between sequential transactions).
3. Return a concise JSON summary: { is_vpn_or_tor: bool, impossible_travel_detected: bool, risk_notes: str }.
```

---

## 5. Backend Implementation Specifications

### 5.1 Dependencies (backend/requirements.txt)
```text
fastapi>=0.110.0
uvicorn>=0.28.0
google-cloud-aiplatform>=1.44.0
google-cloud-firestore>=2.15.0
google-cloud-bigquery>=3.19.0
pydantic>=2.6.0
requests>=2.31.0
httpx>=0.27.0
```

### 5.2 BigQuery Historical Tool (backend/tools/bq_client.py)
```python
import os
from google.cloud import bigquery

client = bigquery.Client(project=os.getenv("GCP_PROJECT"))


def query_historical_stats(user_id: str):
    """Queries user transaction stats over 90 days."""
    query = f"""
    SELECT 
        AVG(amount) as avg_amount,
        STDDEV(amount) as std_amount,
        COUNT(tx_id) as tx_count
    FROM `{os.getenv("GCP_PROJECT")}.fraud_telemetry.historical_txs`
    WHERE user_id = @user_id AND is_fraud = FALSE
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
    )
    result = client.query(query, job_config=job_config).result()
    row = list(result)[0]
    return {
        "avg_amount": float(row.avg_amount or 100.0),
        "std_amount": float(row.std_amount or 15.0),
        "tx_count": int(row.tx_count or 1),
    }
```

### 5.3 Actuator Tool (backend/tools/actuator.py)
```python
import logging


def execute_account_lockout(user_id: str, reason: str) -> dict:
    """Executes account freeze on the banking ledger and triggers alert."""
    logging.info(f"CRITICAL: Freezing account {user_id}. Reason: {reason}")
    # In production, invokes core banking API and triggers WhatsApp/SMS alert
    return {
        "user_id": user_id,
        "action": "ACCOUNT_FROZEN",
        "alert_dispatched": True,
        "status": "SUCCESS",
    }
```

### 5.4 Dockerfile for Cloud Run (backend/Dockerfile)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 6. Frontend Specifications (React + Tailwind)
Key Functional Requirements:
- Live Feed Panel (Left): Display a rolling table of incoming transactions with colored badge pills (CLEAN, SUSPICIOUS, LOCKED).
- Investigation Terminal (Right):
  - Automatically select the currently flagged transaction.
  - Listen directly to doc(db, "investigations", selectedTxId) via Firebase onSnapshot.
  - Render telemetry logs chronologically with typing effect / pill indicators ([Orchestrator], [Behavioral], [ThreatIntel]).
  - SVG Radial Threat Score Meter that animates from 0 to the calculated score.
  - Prominent banner if actuator_action.account_locked == true.
- Manual Simulation Bar (Top):
  - Provide three quick test buttons to let judges trigger tests:
    - Trigger Clean Coffee Purchase ($4.50)
    - Trigger Anomaly: Smurfing Attempt ($9,800)
    - Trigger Anomaly: Impossible Travel Tor Attack ($12,500)

---

## 7. Synthetic Data & Testing Simulation

### 7.1 Dataset Generator (simulation/generate_sims.py)
- Use faker to generate 10,000 baseline transactions across 500 distinct user_id profiles.
- Normal distribution: Mean $75, Std Dev $20, concentrated in local domestic cities.
- Save output to historical_txs.csv and load into BigQuery using bq load.

### 7.2 Adversarial Red-Team Script (simulation/run_adversarial_test.py)
- Generates 500 adversarial edge cases:
  - Velocity Smurfing: 10 micro-transactions ($9,500-$9,990) inside 60 seconds.
  - Impossible Travel: Physical POS swipe in Dubai followed by London e-commerce 12 minutes later.
  - Credential Stuffing Spike: Low-reputation Russian/Tor exit node IP with randomized high amounts.
- Concurrently fires requests to `https://<YOUR_CLOUD_RUN_URL>/api/analyze-tx`.
- Computes and prints evaluation metrics:
  - Accuracy: Target > 98%
  - False Positive Rate: Target < 1.5%
  - Investigation Latency: Target < 2.8 seconds average per case

---

## 8. Development & Deployment Step-by-Step Guide
```bash
# Step 1: GCP Setup & Authentication
gcloud config set project <YOUR_GCP_PROJECT_ID>
gcloud services enable run.googleapis.com aiplatform.googleapis.com firestore.googleapis.com bigquery.googleapis.com

# Step 2: Seed BigQuery Data
python simulation/generate_sims.py
bq mk --dataset <YOUR_GCP_PROJECT_ID>:fraud_telemetry
bq load --source_format=CSV --autodetect fraud_telemetry.historical_txs historical_txs.csv

# Step 3: Deploy Backend to Cloud Run
cd backend
gcloud run deploy aegis-fraud-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT=<YOUR_GCP_PROJECT_ID>

# Step 4: Configure and Deploy Frontend
cd ../frontend
npm install
npm run build
firebase init hosting
firebase deploy --only hosting
```

---

## 9. Submission Deliverables Checklist
- [ ] Working prototype hosted on Google Cloud Run and Firebase Hosting.
- [ ] GitHub repository contains clean code, clear README.md, and architecture diagrams.
- [ ] 3-Minute demonstration video uploaded (showing live agent thought progression in the dashboard).
- [ ] Pitch PDF deck completed highlighting the 40% Technical Merit (Hierarchical ADK structure) and BFSI real-world impact.
