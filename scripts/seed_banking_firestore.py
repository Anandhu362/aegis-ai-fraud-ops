"""Seed authentic enterprise banking data into Google Cloud Firestore.

Populates Firestore collections:
- `customers`: 63 authentic customer identities across 10 US metro regions
- `bank_accounts`: Active checking accounts with routing transit numbers & liquid balances
- `payment_cards`: Masked Visa/Mastercard credentials linked to accounts
- `spending_baselines`: 90-day statistical spending distributions and geofences
"""

import os
import sys

from aegis_common.banking import bank_db
from dotenv import load_dotenv
from google.cloud import firestore

load_dotenv()

BATCH_LIMIT: int = 400


def seed_banking_firestore() -> None:
    """Write all banking database records into Google Cloud Firestore Native collections."""
    project_id = (
        os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "aegis-fraud-ops-2026"
    )
    print(f"[*] Connecting to Google Cloud Firestore (Project: {project_id})...")

    try:
        db = firestore.Client(project=project_id)
    except Exception as exc:
        print(f"[!] Failed to initialize Firestore client: {exc}")
        print("    Ensure GCP credentials (GOOGLE_APPLICATION_CREDENTIALS) are configured.")
        sys.exit(1)

    customers = bank_db.list_all_customers()
    print(f"[*] Seeding {len(customers)} banking customer profiles into Firestore...")

    batch = db.batch()
    batch_count = 0
    total_written = 0

    for record in customers:
        p = record.profile
        # 1. customers collection
        cust_ref = db.collection("customers").document(p.user_id)
        cust_data = {
            "user_id": p.user_id,
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "residential_address": p.residential_address,
            "city": p.city,
            "state": p.state,
            "postal_code": p.postal_code,
            "country": p.country,
            "home_latitude": p.home_latitude,
            "home_longitude": p.home_longitude,
            "kyc_status": p.kyc_status.value,
            "credit_score": p.credit_score,
            "risk_tier": p.risk_tier.value,
            "account_opened_at": p.account_opened_at.isoformat(),
        }
        batch.set(cust_ref, cust_data, merge=True)
        batch_count += 1

        # 2. bank_accounts collection
        for acc in record.accounts:
            acc_ref = db.collection("bank_accounts").document(acc.account_number)
            acc_data = {
                "account_number": acc.account_number,
                "user_id": acc.user_id,
                "routing_number": acc.routing_number,
                "account_type": acc.account_type.value,
                "current_balance": float(acc.current_balance),
                "available_balance": float(acc.available_balance),
                "currency": acc.currency,
                "status": acc.status.value,
            }
            batch.set(acc_ref, acc_data, merge=True)
            batch_count += 1

        # 3. payment_cards collection
        for card in record.cards:
            card_ref = db.collection("payment_cards").document(card.card_token)
            card_data = {
                "card_token": card.card_token,
                "user_id": card.user_id,
                "account_number": card.account_number,
                "masked_pan": card.masked_pan,
                "card_brand": card.card_brand.value,
                "expiry_date": card.expiry_date,
                "daily_spend_limit": float(card.daily_spend_limit),
                "status": card.status.value,
            }
            batch.set(card_ref, card_data, merge=True)
            batch_count += 1

        # 4. spending_baselines collection
        b = record.baseline
        base_ref = db.collection("spending_baselines").document(p.user_id)
        base_data = {
            "user_id": p.user_id,
            "avg_amount": b.avg_amount,
            "std_amount": b.std_amount,
            "median_amount": b.median_amount,
            "p95_amount": b.p95_amount,
            "tx_count_90d": b.tx_count_90d,
            "known_categories": b.known_categories,
            "known_countries": b.known_countries,
            "known_devices": b.known_devices,
            "cold_start": b.cold_start,
        }
        batch.set(base_ref, base_data, merge=True)
        batch_count += 1

        # Commit batch every BATCH_LIMIT operations (Firestore 500 limit)
        if batch_count >= BATCH_LIMIT:
            batch.commit()
            total_written += batch_count
            print(f"    [+] Committed {total_written} documents to Firestore...")
            batch = db.batch()
            batch_count = 0

    if batch_count > 0:
        batch.commit()
        total_written += batch_count

    print(f"\n[OK] Successfully seeded {total_written} total documents into Cloud Firestore:")
    print(f"     - Collection `customers`           ({len(customers)} records)")
    print(f"     - Collection `bank_accounts`       ({len(customers)} records)")
    print(f"     - Collection `payment_cards`       ({len(customers)} records)")
    print(f"     - Collection `spending_baselines`  ({len(customers)} records)")


if __name__ == "__main__":
    seed_banking_firestore()
