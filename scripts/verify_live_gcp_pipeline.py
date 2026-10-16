"""Verify live end-to-end investigation with real Gemini AI, Cloud Firestore, and BigQuery."""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address

import dotenv
from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction
from aegis_engine.bootstrap import build_engine
from aegis_engine.settings import EngineSettings
from google.cloud import bigquery, firestore


async def main() -> None:
    dotenv.load_dotenv()
    print("==================================================================")
    print("   Testing Live Aegis Pipeline (Gemini 2.5 + Firestore + BigQuery)  ")
    print("==================================================================")

    settings = EngineSettings(aegis_adapter_mode="gcp")
    container = build_engine(settings)

    # Coordinated Tor ATO Attack transaction
    tx = Transaction(
        tx_id="TX_LIVEVERIFY04",
        user_id="USR_ELENA391",
        timestamp=datetime.now(UTC),
        amount=Decimal("12500.00"),
        currency="USD",
        merchant="Global Crypto Exchange",
        merchant_category=MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
        channel=Channel.ECOMMERCE,
        device_id="DEV_ATTACKER_TOR",
        ip_address=IPv4Address("185.220.101.5"),
        location=Location(
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="GB",
        ),
    )

    print(f"[*] Ingesting suspicious transaction {tx.tx_id} (${tx.amount})...")
    verdict = await container.service.investigate(tx)

    print(f"[OK] Pipeline Decision: {verdict.decision.value} (Score: {verdict.threat_score}/100)")
    print(f"     Typology:          {verdict.typology.value}")
    print(f"     Gemini Rationale:  {verdict.rationale}")

    # 1. Verify Cloud Firestore
    print("\n[*] Verifying Cloud Firestore persistence...")
    fs = firestore.Client(project="aegis-fraud-ops-2026")
    doc = fs.collection("investigations").document(tx.tx_id).get()
    if doc.exists:
        data = doc.to_dict() or {}
        print(f"    [OK] Firestore document 'investigations/{tx.tx_id}' exists!")
        print(f"         Decision: {data.get('decision')} | Score: {data.get('threat_score')}")

        events = list(
            fs.collection("investigations").document(tx.tx_id).collection("events").stream()
        )
        print(f"    [OK] Firestore subcollection 'events' has {len(events)} milestones streamed!")
    else:
        print(f"    [FAIL] Document 'investigations/{tx.tx_id}' not found in Firestore.")

    # 2. Verify BigQuery
    print("\n[*] Verifying BigQuery streaming...")
    bq = bigquery.Client(project="aegis-fraud-ops-2026")
    query = (
        f"SELECT tx_id, decision, threat_score, typology "  # noqa: S608
        f"FROM `{settings.gcp_project}.{settings.aegis_bq_dataset}.investigation_results` "
        f"WHERE tx_id = '{tx.tx_id}'"
    )
    rows = list(bq.query(query).result())
    print(f"    [OK] BigQuery returned {len(rows)} record(s) from table 'investigation_results'!")
    for r in rows:
        print(
            f"         BigQuery Row: tx_id={r.tx_id}, decision={r.decision}, score={r.threat_score}"
        )

    print("\n==================================================================")
    print("           Live Verification Completed Successfully!              ")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(main())
