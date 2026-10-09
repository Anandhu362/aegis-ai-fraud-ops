"""Deterministic synthetic transaction generation (500 users, 10,000 baseline transactions)."""

import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

from aegis_common.schemas.enums import Channel, MerchantCategory

BENIGN_CATEGORIES = [
    MerchantCategory.COFFEE_SHOP,
    MerchantCategory.GROCERY,
    MerchantCategory.RESTAURANT,
    MerchantCategory.FUEL,
    MerchantCategory.RETAIL,
    MerchantCategory.UTILITIES,
    MerchantCategory.PHARMACY,
]

HIGH_RISK_CATEGORIES = [
    MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    MerchantCategory.GAMBLING,
    MerchantCategory.MONEY_TRANSFER,
]

CITIES = [
    ("San Francisco", "US", 37.7749, -122.4194),
    ("New York", "US", 40.7128, -74.0060),
    ("London", "GB", 51.5074, -0.1278),
    ("Dubai", "AE", 25.2048, 55.2708),
    ("Singapore", "SG", 1.3521, 103.8198),
]


class UserProfile(TypedDict):
    """Internal representation of synthetic customer profile."""

    city: str
    country: str
    lat: float
    lon: float
    avg_spend: float
    device: str
    ip: str


def generate_dataset(
    output_path: Path,
    num_users: int = 500,
    total_txs: int = 10000,
    seed: int = 42,
) -> None:
    """Generate synthetic historical transactions conforming to BigQuery schema.

    Args:
        output_path: Path to output CSV.
        num_users: Number of simulated customer profiles.
        total_txs: Total transactions to emit.
        seed: Random seed for 100% reproducibility.
    """
    random.seed(seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    base_time = datetime(2026, 7, 10, 0, 0, 0, tzinfo=UTC)
    user_ids = [f"USR_{i:04d}" for i in range(1, num_users + 1)]

    # Pre-assign home city and habits to each user
    user_profiles: dict[str, UserProfile] = {}
    for uid in user_ids:
        city, country, lat, lon = random.choice(CITIES)
        avg_spend = random.uniform(25.0, 120.0)
        user_profiles[uid] = {
            "city": city,
            "country": country,
            "lat": lat,
            "lon": lon,
            "avg_spend": avg_spend,
            "device": f"DEV_{uid[4:]}_A",
            "ip": f"73.189.{random.randint(1, 254)}.{random.randint(1, 254)}",
        }

    tx_rows: list[dict[str, Any]] = []
    fieldnames = [
        "tx_id",
        "user_id",
        "ts",
        "amount",
        "currency",
        "merchant",
        "merchant_category",
        "channel",
        "device_id",
        "ip_address",
        "latitude",
        "longitude",
        "city",
        "country",
        "is_fraud",
        "fraud_type",
    ]

    for idx in range(1, total_txs + 1):
        tx_id = f"TX_{idx:06d}"
        uid = random.choice(user_ids)
        uprof = user_profiles[uid]

        # 98.5% Benign, 1.5% Fraud (matches real-world BFSI distributions)
        is_fraud = random.random() < 0.015
        delta_days = random.uniform(0, 90)
        delta_seconds = random.uniform(0, 86400)
        ts = base_time + timedelta(days=delta_days, seconds=delta_seconds)

        if not is_fraud:
            # Benign transaction
            category = random.choice(BENIGN_CATEGORIES)
            amount = max(2.50, round(random.gauss(uprof["avg_spend"], uprof["avg_spend"] * 0.3), 2))
            channel = random.choice([Channel.CARD_PRESENT, Channel.ECOMMERCE])
            fraud_type = ""
            city, country, lat, lon = (
                uprof["city"],
                uprof["country"],
                uprof["lat"],
                uprof["lon"],
            )
            device = uprof["device"]
            ip = uprof["ip"]
        else:
            # Fraudulent transaction
            fraud_type = random.choice(["ACCOUNT_TAKEOVER", "STRUCTURING"])
            if fraud_type == "STRUCTURING":
                amount = round(random.uniform(8500.0, 9950.0), 2)
                category = MerchantCategory.MONEY_TRANSFER
                channel = Channel.ECOMMERCE
                city, country, lat, lon = (
                    uprof["city"],
                    uprof["country"],
                    uprof["lat"],
                    uprof["lon"],
                )
                device = uprof["device"]
                ip = uprof["ip"]
            else:  # ACCOUNT_TAKEOVER
                amount = round(random.uniform(5000.0, 25000.0), 2)
                category = random.choice(HIGH_RISK_CATEGORIES)
                channel = Channel.ECOMMERCE
                # Destination London or Dubai over Tor
                city, country, lat, lon = ("London", "GB", 51.5074, -0.1278)
                device = f"DEV_HACK_{idx}"
                ip = "185.220.101.5"

        tx_rows.append(
            {
                "tx_id": tx_id,
                "user_id": uid,
                "ts": ts.isoformat(),
                "amount": amount,
                "currency": "USD",
                "merchant": f"Merchant {category.value.title()}",
                "merchant_category": category.value,
                "channel": channel.value,
                "device_id": device,
                "ip_address": ip,
                "latitude": lat,
                "longitude": lon,
                "city": city,
                "country": country,
                "is_fraud": is_fraud,
                "fraud_type": fraud_type,
            }
        )

    # Sort chronologically by timestamp
    tx_rows.sort(key=lambda r: str(r["ts"]))

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tx_rows)

    print(f"Generated {len(tx_rows)} synthetic transactions -> {output_path}")


if __name__ == "__main__":
    target_csv = Path(__file__).resolve().parent.parent.parent / "data" / "historical_txs.csv"
    generate_dataset(target_csv, num_users=500, total_txs=10000)
