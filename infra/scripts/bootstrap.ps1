<#
.SYNOPSIS
    Aegis AI Fraud Ops - Google Cloud and Firebase Bootstrap Script
.DESCRIPTION
    Automates the initialization of GCP project APIs, Firestore Native database,
    Service Accounts, least-privilege IAM roles, Pub/Sub topics, BigQuery telemetry dataset,
    Secret Manager, and Google Maps Platform APIs.
.PARAMETER ProjectId
    The Google Cloud Project ID (defaults to GCP_PROJECT from .env or current gcloud config).
.PARAMETER Region
    The GCP compute and Vertex AI region (default: us-central1).
.PARAMETER FirestoreRegion
    The Firestore database location (default: us-central1).
.PARAMETER GenerateDevKeys
    Switch to export service account credentials to infra/keys/ for local testing.
.PARAMETER EnableMaps
    Switch to enable Google Maps Platform APIs (Maps JS and Geocoding).
#>

[CmdletBinding()]
param(
    [string]$ProjectId = '',
    [string]$Region = 'us-central1',
    [string]$FirestoreRegion = 'us-central1',
    [switch]$GenerateDevKeys,
    [switch]$EnableMaps = $true
)

$ErrorActionPreference = 'Continue'

Write-Host '==================================================================' -ForegroundColor Cyan
Write-Host '       Aegis AI Fraud Ops - Google Cloud Ecosystem Bootstrap       ' -ForegroundColor Cyan
Write-Host '==================================================================' -ForegroundColor Cyan

# 1. Verify gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host 'ERROR: Google Cloud SDK (gcloud) is not found in PATH.' -ForegroundColor Red
    exit 1
}

# 2. Determine Project ID
if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    if (Test-Path '.env') {
        $envMatch = Select-String -Path '.env' -Pattern '^GCP_PROJECT=(.+)$'
        if ($envMatch) {
            $ProjectId = $envMatch.Matches[0].Groups[1].Value.Trim()
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    $ProjectId = (gcloud config get-value project 2>$null).Trim()
}

if ([string]::IsNullOrWhiteSpace($ProjectId)) {
    Write-Host 'ERROR: GCP Project ID could not be determined. Pass -ProjectId [your-project-id].' -ForegroundColor Red
    exit 1
}

Write-Host "[*] Target GCP Project: $ProjectId" -ForegroundColor Green
Write-Host "[*] Target Region:      $Region" -ForegroundColor Green
Write-Host "[*] Firestore Region:   $FirestoreRegion" -ForegroundColor Green
Write-Host ''

gcloud config set project $ProjectId --quiet

# 3. Enable Required Google Cloud APIs
Write-Host '--> [1/7] Enabling required Google Cloud APIs...' -ForegroundColor Yellow
$RequiredApis = @(
    'run.googleapis.com',              # Cloud Run microservices
    'aiplatform.googleapis.com',       # Vertex AI and Gemini Models
    'firestore.googleapis.com',        # Cloud Firestore (Native mode)
    'bigquery.googleapis.com',         # BigQuery behavioral baselines and telemetry
    'pubsub.googleapis.com',           # Pub/Sub asynchronous event ingestion
    'secretmanager.googleapis.com',    # Secret Manager for API keys and tokens
    'artifactregistry.googleapis.com', # Container images
    'cloudscheduler.googleapis.com',   # Cron schedules for analytics jobs
    'iamcredentials.googleapis.com'    # Workload identity and token creation
)

if ($EnableMaps) {
    $RequiredApis += @(
        'maps-backend.googleapis.com',     # Google Maps SDK / JavaScript API
        'geocoding-backend.googleapis.com' # Geocoding API for location intelligence
    )
}

foreach ($api in $RequiredApis) {
    Write-Host "    Checking / Enabling $api..."
    gcloud services enable $api --project $ProjectId --quiet
}
Write-Host '    [OK] APIs successfully enabled.' -ForegroundColor Green

# 4. Initialize Firestore Database in Native Mode
Write-Host "`n--> [2/7] Initializing Firestore Native Database..." -ForegroundColor Yellow
$ExistingDb = (gcloud firestore databases list --project $ProjectId --format='value(name)' 2>&1)
if (-not ($ExistingDb -match 'databases/\(default\)')) {
    Write-Host "    Creating Firestore (default) database in Native mode ($FirestoreRegion)..."
    gcloud firestore databases create --location=$FirestoreRegion --type=firestore-native --project $ProjectId --quiet
    Write-Host '    [OK] Firestore database created.' -ForegroundColor Green
} else {
    Write-Host '    [OK] Firestore database already exists.' -ForegroundColor Green
}

# 5. Create Artifact Registry Docker Repository
Write-Host "`n--> [3/7] Setting up Artifact Registry..." -ForegroundColor Yellow
$ExistingRepos = (gcloud artifacts repositories list --location=$Region --project $ProjectId --format='value(name)' 2>&1)
if (-not ($ExistingRepos -match 'repositories/aegis')) {
    Write-Host "    Creating Docker repository 'aegis' in $Region..."
    gcloud artifacts repositories create aegis --repository-format=docker --location=$Region --description='Aegis container images' --project $ProjectId --quiet
    Write-Host "    [OK] Artifact Registry repository 'aegis' created." -ForegroundColor Green
} else {
    Write-Host "    [OK] Artifact Registry repository 'aegis' already exists." -ForegroundColor Green
}

# 6. Create Pub/Sub Topics
Write-Host "`n--> [4/7] Setting up Pub/Sub topics..." -ForegroundColor Yellow
$ExistingTopics = (gcloud pubsub topics list --project $ProjectId --format='value(name)' 2>&1)
$Topics = @('tx-ingest', 'tx-ingest-dlq')
foreach ($top in $Topics) {
    if (-not ($ExistingTopics -match "topics/$top")) {
        Write-Host "    Creating topic '$top'..."
        gcloud pubsub topics create $top --project $ProjectId --quiet
    } else {
        Write-Host "    Topic '$top' already exists."
    }
}
Write-Host '    [OK] Pub/Sub topics configured.' -ForegroundColor Green

# 7. Create BigQuery Dataset
Write-Host "`n--> [5/7] Setting up BigQuery dataset 'fraud_telemetry'..." -ForegroundColor Yellow
$token = (gcloud auth print-access-token 2>$null).Trim()
$bqHeaders = @{ 'Authorization' = "Bearer $token"; 'Content-Type' = 'application/json' }
$checkUri = "https://bigquery.googleapis.com/bigquery/v2/projects/$ProjectId/datasets/fraud_telemetry"
$exists = $false
try {
    $null = Invoke-RestMethod -Method GET -Uri $checkUri -Headers $bqHeaders -ErrorAction Stop
    $exists = $true
} catch {
    $exists = $false
}

if (-not $exists) {
    Write-Host "    Creating dataset 'fraud_telemetry'..."
    $body = @{ 'datasetReference' = @{ 'datasetId' = 'fraud_telemetry'; 'projectId' = $ProjectId }; 'location' = 'US' } | ConvertTo-Json
    $null = Invoke-RestMethod -Method POST -Uri "https://bigquery.googleapis.com/bigquery/v2/projects/$ProjectId/datasets" -Headers $bqHeaders -Body $body
    Write-Host '    [OK] BigQuery dataset created.' -ForegroundColor Green
} else {
    Write-Host "    [OK] BigQuery dataset 'fraud_telemetry' already exists." -ForegroundColor Green
}

# 8. Create Service Accounts and Assign Least-Privilege IAM Roles
Write-Host "`n--> [6/7] Creating Service Accounts and Binding IAM Roles..." -ForegroundColor Yellow

$ServiceAccounts = @{
    'sa-gateway' = @(
        'roles/datastore.user',
        'roles/pubsub.publisher',
        'roles/secretmanager.secretAccessor',
        'roles/run.invoker'
    );
    'sa-agent-engine' = @(
        'roles/aiplatform.user',
        'roles/datastore.user',
        'roles/bigquery.dataViewer',
        'roles/bigquery.jobUser',
        'roles/bigquery.dataEditor',
        'roles/run.invoker'
    );
    'sa-actuator' = @(
        'roles/datastore.user',
        'roles/secretmanager.secretAccessor'
    );
    'sa-pubsub-invoker' = @(
        'roles/run.invoker'
    );
    'sa-jobs' = @(
        'roles/bigquery.jobUser',
        'roles/bigquery.dataEditor',
        'roles/datastore.user',
        'roles/storage.objectAdmin'
    )
}

$ExistingSAs = (gcloud iam service-accounts list --project $ProjectId --format='value(email)' 2>&1)

foreach ($sa in $ServiceAccounts.Keys) {
    $saEmail = "$sa@$ProjectId.iam.gserviceaccount.com"
    if (-not ($ExistingSAs -match $saEmail)) {
        Write-Host "    Creating Service Account '$sa'..."
        gcloud iam service-accounts create $sa --display-name="Aegis $sa" --project $ProjectId --quiet
    } else {
        Write-Host "    Service Account '$sa' already exists."
    }

    # Bind roles
    foreach ($role in $ServiceAccounts[$sa]) {
        Write-Host "      Binding $role to $sa..."
        gcloud projects add-iam-policy-binding $ProjectId `
            --member="serviceAccount:$saEmail" `
            --role=$role `
            --condition=None `
            --quiet > $null
    }
}
Write-Host '    [OK] Service accounts and IAM roles bound.' -ForegroundColor Green

# 9. Secret Manager Secrets Initialization
Write-Host "`n--> [7/7] Checking Secret Manager..." -ForegroundColor Yellow
$ExistingSecrets = (gcloud secrets list --project $ProjectId --format='value(name)' 2>&1)
if (-not ($ExistingSecrets -match 'secrets/aegis-api-keys')) {
    Write-Host "    Creating secret 'aegis-api-keys'..."
    gcloud secrets create aegis-api-keys --replication-policy='automatic' --project $ProjectId --quiet
    $devSecretContent = '{"simulator-dev":"b89e3a9c7b949be4b3f81e6267885b19d454641e17d66d7e0026e63787fb9ff3"}'
    $devSecretContent | gcloud secrets versions add aegis-api-keys --data-file=- --project $ProjectId --quiet
    Write-Host "    [OK] Secret 'aegis-api-keys' created." -ForegroundColor Green
} else {
    Write-Host "    [OK] Secret 'aegis-api-keys' already exists." -ForegroundColor Green
}

# Optional: Export Development Service Account Key
if ($GenerateDevKeys) {
    Write-Host "`n--> [Optional] Generating local development key for sa-agent-engine..." -ForegroundColor Yellow
    $KeyDir = 'infra/keys'
    if (-not (Test-Path $KeyDir)) {
        New-Item -ItemType Directory -Path $KeyDir | Out-Null
    }
    $KeyPath = "$KeyDir/sa-agent-engine.json"
    gcloud iam service-accounts keys create $KeyPath `
        --iam-account="sa-agent-engine@$ProjectId.iam.gserviceaccount.com" `
        --project $ProjectId --quiet
    Write-Host "    [OK] Key exported to $KeyPath (strictly ignored by .gitignore)." -ForegroundColor Green
    Write-Host "    To use locally: `$env:GOOGLE_APPLICATION_CREDENTIALS='$KeyPath'" -ForegroundColor Cyan
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host '       GCP and Firebase Ecosystem Initialization Complete!        ' -ForegroundColor Green
Write-Host '==================================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Summary of Resources:'
Write-Host "  Project:          $ProjectId"
Write-Host "  Firestore:        (default) Native Mode ($FirestoreRegion)"
Write-Host "  Artifact Repo:    us-central1-docker.pkg.dev/$ProjectId/aegis"
Write-Host '  Pub/Sub:          tx-ingest, tx-ingest-dlq'
Write-Host "  BigQuery:         $ProjectId:fraud_telemetry"
Write-Host '  Service Accounts: sa-gateway, sa-agent-engine, sa-actuator, sa-pubsub-invoker, sa-jobs'
Write-Host ''
Write-Host "Next Step: You can run 'py -m uv run python scripts/check_models.py' to verify Gemini."
Write-Host ''
