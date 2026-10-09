#!/usr/bin/env bash
# ==============================================================================
# Aegis AI Fraud Ops — Google Cloud & Firebase Bootstrap Script
# ==============================================================================
set -euo pipefail

PROJECT_ID="${1:-${GCP_PROJECT:-}}"
REGION="${2:-us-central1}"
FIRESTORE_REGION="${3:-us-central1}"
GENERATE_DEV_KEYS="${4:-false}"

echo "=================================================================="
echo "       Aegis AI Fraud Ops — Google Cloud Ecosystem Bootstrap       "
echo "=================================================================="

if ! command -v gcloud &> /dev/null; then
    echo "ERROR: Google Cloud SDK ('gcloud') is not found in PATH." >&2
    exit 1
fi

if [[ -z "$PROJECT_ID" ]]; then
    if [[ -f .env ]]; then
        PROJECT_ID=$(grep -E '^GCP_PROJECT=' .env | cut -d '=' -f2 | tr -d ' "')
    fi
fi

if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || true)
fi

if [[ -z "$PROJECT_ID" ]]; then
    echo "ERROR: GCP Project ID could not be determined. Usage: ./bootstrap.sh <project-id>" >&2
    exit 1
fi

echo "[*] Target GCP Project: $PROJECT_ID"
echo "[*] Target Region:      $REGION"
echo "[*] Firestore Region:   $FIRESTORE_REGION"
echo ""

gcloud config set project "$PROJECT_ID" --quiet

# 1. Enable Required APIs
echo "--> [1/7] Enabling required Google Cloud APIs..."
APIS=(
    "run.googleapis.com"
    "aiplatform.googleapis.com"
    "firestore.googleapis.com"
    "bigquery.googleapis.com"
    "pubsub.googleapis.com"
    "secretmanager.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudscheduler.googleapis.com"
    "iamcredentials.googleapis.com"
    "maps-backend.googleapis.com"
    "geocoding-backend.googleapis.com"
)
for api in "${APIS[@]}"; do
    echo "    Enabling $api..."
    gcloud services enable "$api" --project "$PROJECT_ID" --quiet
done

# 2. Firestore Native Database
echo "--> [2/7] Initializing Firestore Native Database..."
if ! gcloud firestore databases list --project "$PROJECT_ID" --format="value(name)" | grep -q "default"; then
    echo "    Creating Firestore (default) database in Native mode ($FIRESTORE_REGION)..."
    gcloud firestore databases create --location="$FIRESTORE_REGION" --type=firestore-native --project "$PROJECT_ID" --quiet
else
    echo "    [OK] Firestore database already exists."
fi

# 3. Artifact Registry
echo "--> [3/7] Setting up Artifact Registry..."
if ! gcloud artifacts repositories describe aegis --location="$REGION" --project "$PROJECT_ID" &>/dev/null; then
    echo "    Creating Docker repository 'aegis' in $REGION..."
    gcloud artifacts repositories create aegis --repository-format=docker --location="$REGION" --description="Aegis container images" --project "$PROJECT_ID" --quiet
else
    echo "    [OK] Artifact Registry repository 'aegis' already exists."
fi

# 4. Pub/Sub Topics
echo "--> [4/7] Setting up Pub/Sub topics..."
for top in tx-ingest tx-ingest-dlq; do
    if ! gcloud pubsub topics describe "$top" --project "$PROJECT_ID" &>/dev/null; then
        echo "    Creating topic '$top'..."
        gcloud pubsub topics create "$top" --project "$PROJECT_ID" --quiet
    else
        echo "    Topic '$top' already exists."
    fi
done

# 5. BigQuery Dataset
echo "--> [5/7] Setting up BigQuery dataset 'fraud_telemetry'..."
if ! bq show --project_id="$PROJECT_ID" fraud_telemetry &>/dev/null; then
    echo "    Creating dataset 'fraud_telemetry'..."
    bq --location=US mk --dataset "$PROJECT_ID:fraud_telemetry"
else
    echo "    [OK] BigQuery dataset 'fraud_telemetry' already exists."
fi

# 6. Service Accounts and IAM Roles
echo "--> [6/7] Creating Service Accounts & Binding IAM Roles..."
declare -A SA_ROLES
SA_ROLES["sa-gateway"]="roles/datastore.user roles/pubsub.publisher roles/secretmanager.secretAccessor roles/run.invoker"
SA_ROLES["sa-agent-engine"]="roles/aiplatform.user roles/datastore.user roles/bigquery.dataViewer roles/bigquery.jobUser roles/bigquery.dataEditor roles/run.invoker"
SA_ROLES["sa-actuator"]="roles/datastore.user roles/secretmanager.secretAccessor"
SA_ROLES["sa-pubsub-invoker"]="roles/run.invoker"
SA_ROLES["sa-jobs"]="roles/bigquery.jobUser roles/bigquery.dataEditor roles/datastore.user roles/storage.objectAdmin"

for sa in "${!SA_ROLES[@]}"; do
    sa_email="$sa@$PROJECT_ID.iam.gserviceaccount.com"
    if ! gcloud iam service-accounts describe "$sa_email" --project "$PROJECT_ID" &>/dev/null; then
        echo "    Creating Service Account '$sa'..."
        gcloud iam service-accounts create "$sa" --display-name="Aegis $sa" --project "$PROJECT_ID" --quiet
    else
        echo "    Service Account '$sa' already exists."
    fi

    for role in ${SA_ROLES[$sa]}; do
        echo "      Binding $role to $sa..."
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$sa_email" \
            --role="$role" \
            --condition=None \
            --quiet > /dev/null
    done
done

# 7. Secret Manager
echo "--> [7/7] Checking Secret Manager..."
if ! gcloud secrets describe aegis-api-keys --project "$PROJECT_ID" &>/dev/null; then
    echo "    Creating secret 'aegis-api-keys'..."
    gcloud secrets create aegis-api-keys --replication-policy="automatic" --project "$PROJECT_ID" --quiet
    echo '{"simulator-dev":"b89e3a9c7b949be4b3f81e6267885b19d454641e17d66d7e0026e63787fb9ff3"}' | \
        gcloud secrets versions add aegis-api-keys --data-file=- --project "$PROJECT_ID" --quiet
else
    echo "    [OK] Secret 'aegis-api-keys' already exists."
fi

# Optional dev keys
if [[ "$GENERATE_DEV_KEYS" == "true" ]]; then
    mkdir -p infra/keys
    gcloud iam service-accounts keys create infra/keys/sa-agent-engine.json \
        --iam-account="sa-agent-engine@$PROJECT_ID.iam.gserviceaccount.com" \
        --project "$PROJECT_ID" --quiet
    echo "[OK] Key exported to infra/keys/sa-agent-engine.json (gitignored)."
fi

echo "=================================================================="
echo "       GCP & Firebase Ecosystem Initialization Complete!        "
echo "=================================================================="
