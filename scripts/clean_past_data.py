"""Purge past investigation test data from Google Cloud Firestore, BigQuery, memory hot-caches, and banking states.

Cleans up past simulation transactions so the SOC Dashboard starts completely fresh,
flushes Gateway hot-caches, pushes real-time reset events to open browser tabs,
and restores all customer accounts, balances, and card statuses to ACTIVE.
"""

# ruff: noqa: E402, E501, PLR0915, S310

import json
import os
import sys
import urllib.error
import urllib.request

import dotenv
from google.cloud import bigquery, firestore

# Add common package to path if needed
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(WORKSPACE_ROOT, "packages", "aegis-common", "src"))
from aegis_common.banking import bank_db


def main() -> None:
    dotenv.load_dotenv(override=True)
    project_id = os.getenv("GCP_PROJECT", "aegis-fraud-ops-2026")
    gateway_url = os.getenv("AEGIS_GATEWAY_URL", "http://127.0.0.1:8080")

    print("==================================================================")
    print("      Aegis Fraud Ops - Past Data Purge & Dashboard Reset         ")
    print("==================================================================")
    print(f"[*] Cloud Firestore Project: {project_id}")
    print("[*] Target Collection:       'investigations'")
    print(f"[*] Gateway Service Probe:   {gateway_url}")
    print("------------------------------------------------------------------")

    gateway_cleared = False

    # 1. Probe running API Gateway and trigger in-memory & real-time broadcast reset
    try:
        req = urllib.request.Request(
            f"{gateway_url}/v1/investigations:clear",
            data=b"{}",
            headers={"Content-Type": "application/json", "User-Agent": "AegisCleaner/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if resp.status in (200, 204):
                body = resp.read().decode("utf-8")
                data = json.loads(body) if body else {}
                count = data.get("cleared_count", "all")
                print(
                    f"[OK] Live API Gateway hot-cache flushed ({count} cases purged). "
                    "Real-time reset broadcast pushed to browser dashboard!"
                )
                gateway_cleared = True
    except Exception as exc:
        print(
            f"[*] API Gateway offline or not reached ({exc}). Proceeding with direct storage purge..."
        )

    # 2. Purge Firestore investigations collection
    try:
        db = firestore.Client(project=project_id)
        docs = list(db.collection("investigations").stream())
        doc_count = len(docs)

        if doc_count > 0:
            print(f"[*] Found {doc_count} legacy investigation records in Firestore.")
            for i in range(0, doc_count, 400):
                batch = db.batch()
                chunk = docs[i : i + 400]
                for doc in chunk:
                    batch.delete(doc.reference)
                batch.commit()
                print(f"    [OK] Deleted batch of {len(chunk)} documents...")
            print(
                f"[OK] Successfully purged {doc_count} past investigation records from Firestore Native!"
            )
        else:
            print("[OK] Firestore 'investigations' collection is clean (0 documents).")

    except Exception as exc:
        print(f"[!] Warning: Firestore purge encountered an error: {exc}")

    # 3. Truncate BigQuery investigation_results if available
    try:
        bq = bigquery.Client(project=project_id)
        bq.query("TRUNCATE TABLE fraud_telemetry.investigation_results").result()
        print("[OK] Successfully truncated BigQuery 'fraud_telemetry.investigation_results'!")
    except Exception as exc:
        print(f"[!] Note: BigQuery truncate skipped or unavailable: {exc}")

    # 4. Reset Core Banking Database Accounts and Cards to ACTIVE
    print("\n[*] Resetting Banking Database customer states and transaction histories...")
    reset_count = bank_db.reset_all()
    print(f"[OK] Restored {reset_count} customer bank accounts and payment cards to ACTIVE status.")

    print("==================================================================")
    print("          DASHBOARD AND DATABASE ARE FRESH & READY!               ")
    print("==================================================================")
    if gateway_cleared:
        print(">> Live dashboard has already updated to 0 cases in real-time.")
    else:
        print(">> Start or restart your services (.\\run_system.ps1) to see")
        print("   a fresh, clean SOC dashboard awaiting new transactions.")
    print("------------------------------------------------------------------\n")


if __name__ == "__main__":
    main()
