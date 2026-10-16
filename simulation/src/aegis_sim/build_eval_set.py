"""Generate 2,000 balanced, reproducible evaluation cases for red-team testing (AEG-60).

Comprises:
- 1,500 Benign everyday transactions (expected ALLOW, is_fraud=False)
- 200 Account Takeover / Impossible Travel cases (expected LOCK_ACCOUNT, is_fraud=True)
- 200 Structuring / Smurfing cases (expected BLOCK_TX, is_fraud=True)
- 100 Novel Merchant Deviation cases (expected REVIEW, is_fraud=True)
"""

import argparse
import hashlib
import json
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction

CITIES = [
    ("San Francisco", "US", 37.7749, -122.4194),
    ("New York", "US", 40.7128, -74.0060),
    ("London", "GB", 51.5074, -0.1278),
    ("Dubai", "AE", 25.2048, 55.2708),
    ("Singapore", "SG", 1.3521, 103.8198),
    ("Tokyo", "JP", 35.6762, 139.6503),
]


BENIGN_CITIES = [
    ("San Francisco", "US", 37.7749, -122.4194),
    ("New York", "US", 40.7128, -74.0060),
    ("Seattle", "US", 47.6062, -122.3321),
    ("Austin", "US", 30.2672, -97.7431),
]


def generate_eval_cases(count: int = 2000, seed: int = 42) -> list[dict[str, Any]]:
    """Generate deterministically seeded evaluation cases."""
    random.seed(seed)
    cases: list[dict[str, Any]] = []

    benign_count = int(count * 0.75)  # 1500 of 2000
    ato_count = int(count * 0.10)  # 200 of 2000
    smurf_count = int(count * 0.10)  # 200 of 2000
    dev_count = count - (benign_count + ato_count + smurf_count)  # 100 of 2000

    base_time = datetime(2026, 10, 10, 12, 0, 0, tzinfo=UTC)

    # 1. Benign cases (1500)
    for i in range(1, benign_count + 1):
        city, country, lat, lon = random.choice(BENIGN_CITIES)
        amount = round(random.uniform(3.50, 85.00), 2)
        category = random.choice(
            [
                MerchantCategory.COFFEE_SHOP,
                MerchantCategory.GROCERY,
                MerchantCategory.RESTAURANT,
                MerchantCategory.FUEL,
                MerchantCategory.UTILITIES,
            ]
        )
        tx = Transaction(
            tx_id=f"TX_BENIGN{i:05d}",
            user_id=f"USR_BN{i:05d}",
            timestamp=base_time + timedelta(minutes=i * 2),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant=f"Local Merchant {random.randint(10, 99)}",
            merchant_category=category,
            channel=random.choice([Channel.CARD_PRESENT, Channel.ECOMMERCE]),
            device_id=f"DEV_KNOWN_{i:05d}",
            ip_address=f"73.189.{random.randint(10, 200)}.{random.randint(2, 250)}",  # type: ignore[arg-type]
            location=Location(latitude=lat, longitude=lon, city=city, country=country),
        )
        cases.append(
            {
                "case_id": tx.tx_id,
                "scenario": "BENIGN",
                "is_fraud": False,
                "expected_decision": "ALLOW",
                "expected_typology": "NONE",
                "transaction": tx.model_dump(mode="json"),
            }
        )

    # 2. Account Takeover / Impossible travel (200)
    for i in range(1, ato_count + 1):
        # Tor exit node or VPN with high velocity travel jump
        amount = round(random.uniform(4500.00, 15000.00), 2)
        tx = Transaction(
            tx_id=f"TX_ATO{i:05d}",
            user_id=f"USR_ATO{i:04d}",
            timestamp=base_time + timedelta(minutes=i * 5),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant="Crypto Liquidity Gate Inc",
            merchant_category=MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
            channel=Channel.ECOMMERCE,
            device_id=f"DEV_UNKNOWN_{i:04d}",
            ip_address="185.220.101.5",  # type: ignore[arg-type]
            location=Location(latitude=51.5074, longitude=-0.1278, city="London", country="GB"),
        )
        cases.append(
            {
                "case_id": tx.tx_id,
                "scenario": "ACCOUNT_TAKEOVER",
                "is_fraud": True,
                "expected_decision": "LOCK_ACCOUNT",
                "expected_typology": "ACCOUNT_TAKEOVER",
                "transaction": tx.model_dump(mode="json"),
            }
        )

    # 3. Structuring / Smurfing (200)
    for i in range(1, smurf_count + 1):
        amount = round(random.uniform(9100.00, 9950.00), 2)
        tx = Transaction(
            tx_id=f"TX_SMURF{i:05d}",
            user_id=f"USR_SMRF{i:04d}",
            timestamp=base_time + timedelta(minutes=i * 3),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant="Express Money Transfer LLC",
            merchant_category=MerchantCategory.MONEY_TRANSFER,
            channel=Channel.ECOMMERCE,
            device_id=f"DEV_SMURF_{i:04d}",
            ip_address=f"198.51.100.{random.randint(1, 254)}",  # type: ignore[arg-type]
            location=Location(latitude=40.7128, longitude=-74.0060, city="New York", country="US"),
        )
        cases.append(
            {
                "case_id": tx.tx_id,
                "scenario": "STRUCTURING",
                "is_fraud": True,
                "expected_decision": "BLOCK_TX",
                "expected_typology": "STRUCTURING",
                "transaction": tx.model_dump(mode="json"),
            }
        )

    # 4. Merchant Category Deviation / Unusual high-risk activity (100)
    for i in range(1, dev_count + 1):
        amount = round(random.uniform(2200.00, 4800.00), 2)
        tx = Transaction(
            tx_id=f"TX_DEV{i:05d}",
            user_id=f"USR_DEV{i:04d}",
            timestamp=base_time + timedelta(minutes=i * 7),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant="Monte Carlo Premier Gaming",
            merchant_category=MerchantCategory.GAMBLING,
            channel=Channel.ECOMMERCE,
            device_id=f"DEV_BROWSER_{i:04d}",
            ip_address=f"203.0.113.{random.randint(1, 254)}",  # type: ignore[arg-type]
            location=Location(latitude=43.7384, longitude=7.4246, city="Monaco", country="MC"),
        )
        cases.append(
            {
                "case_id": tx.tx_id,
                "scenario": "MERCHANT_DEVIATION",
                "is_fraud": True,
                "expected_decision": "REVIEW",
                "expected_typology": "MERCHANT_DEVIATION",
                "transaction": tx.model_dump(mode="json"),
            }
        )

    # Shuffle to interleave while keeping determinism
    random.shuffle(cases)
    return cases


def build_and_save(output_file: Path, count: int = 2000, seed: int = 42) -> str:
    """Build dataset, write JSON, and return sha256 checksum."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cases = generate_eval_cases(count=count, seed=seed)

    content = json.dumps(cases, indent=2)
    output_file.write_text(content, encoding="utf-8")

    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    metadata_file = output_file.with_suffix(".meta.json")
    metadata = {
        "dataset_name": output_file.name,
        "total_cases": len(cases),
        "benign_cases": sum(1 for c in cases if not c["is_fraud"]),
        "adversarial_cases": sum(1 for c in cases if c["is_fraud"]),
        "seed": seed,
        "sha256": sha,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    metadata_file.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return sha


def main() -> None:
    """CLI entrypoint for AEG-60 dataset builder."""
    desc = "Build Aegis red-team evaluation dataset (AEG-60)."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent / "data" / "eval_set_2000.json",
        help="Path to output JSON file",
    )
    parser.add_argument("--count", type=int, default=2000, help="Total cases (default: 2000)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args()

    sha = build_and_save(args.output, count=args.count, seed=args.seed)
    print(f"Successfully generated {args.count} evaluation cases in {args.output}")
    print(f"Dataset SHA-256: {sha}")


if __name__ == "__main__":
    main()
