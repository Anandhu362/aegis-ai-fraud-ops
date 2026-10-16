"""Generate and stream 10,000 real-world consumer financial transactions.

Simulates genuine human behavior at enterprise banking scale with:
- Authentic BFSI banking customer personas (real names, checking accounts, cards, devices)
- 90-day past historical baseline spend and location consistency
- Natural human observation pacing (deliberate 2.0s - 3.5s Poisson intervals)
- 95.0% Organic benign everyday purchases (fast-path triage, < 20ms, $0 tokens)
-  2.5% Account Takeover / Impossible Travel attacks (Tor/VPN exit nodes, autonomous lockout)
-  2.0% BSA Structuring / Smurfing attacks (near-$10k transfers, deterministic block)
-  0.5% 3DS Step-Up Challenge (unrecognized new devices, out-of-band verification)
- Live checking balance debiting and account freeze containment in banking database.
"""

import argparse
import asyncio
import hashlib
import json
import random
import sys
import time
from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any

# Force line-buffering and UTF-8 on Windows terminal stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

import httpx
from aegis_common.banking import bank_db
from aegis_common.schemas.banking import BankingCustomerRecord
from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction

MERCHANTS: dict[MerchantCategory, list[str]] = {
    MerchantCategory.COFFEE_SHOP: [
        "Blue Bottle Coffee",
        "Starbucks Reserve",
        "Philz Coffee",
        "Sightglass Roastery",
        "Local Craft Bakery",
    ],
    MerchantCategory.GROCERY: [
        "Whole Foods Market",
        "Trader Joe's",
        "Safeway Organics",
        "Sprouts Farmers Market",
        "Wegmans Food Market",
    ],
    MerchantCategory.RESTAURANT: [
        "Sweetgreen Farm Stand",
        "Chipotle Mexican Grill",
        "Shake Shack",
        "Nobu Downtown",
        "Trattoria Rustica",
        "Mendocino Farms",
        "Din Tai Fung",
    ],
    MerchantCategory.FUEL: [
        "Chevron Fuel Station",
        "Shell Oil",
        "ExxonMobil",
        "7-Eleven Express Fuel",
        "Mobil Express",
    ],
    MerchantCategory.RETAIL: [
        "Target Stores",
        "Apple Store Fifth Ave",
        "Nordstrom Rack",
        "Amazon Go Retail",
        "REI Outdoor Goods",
        "Sephora Beauty",
    ],
    MerchantCategory.ELECTRONICS: [
        "Apple Store Fifth Ave",
        "Best Buy Electronics Direct",
        "B&H Photo Video NYC",
        "Micro Center Technology",
    ],
    MerchantCategory.UTILITIES: [
        "Pacific Gas & Electric",
        "Con Edison New York",
        "AT&T Fiber Mobility",
        "Verizon Wireless Fios",
    ],
    MerchantCategory.TRAVEL: [
        "Delta Air Lines",
        "United Airlines",
        "Uber Technologies",
        "Lyft Rideshare",
        "Marriott International",
    ],
    MerchantCategory.PHARMACY: [
        "CVS Pharmacy",
        "Walgreens Health",
        "Duane Reade",
    ],
    MerchantCategory.ENTERTAINMENT: [
        "AMC Theatres",
        "Netflix Streaming",
        "Spotify USA",
    ],
    MerchantCategory.CRYPTOCURRENCY_BROKERAGE: [
        "Apex Global Crypto Liquidity",
        "BitVault Offshore Assets",
        "Eastern European Liquidity Hub",
        "Offshore Crypto Gateway International",
    ],
    MerchantCategory.MONEY_TRANSFER: [
        "Express Money Transfer Systems LLC",
        "Global Remittance Express",
        "WireDirect Remittance Hub",
    ],
    MerchantCategory.GAMBLING: [
        "Monaco Grand Casino Resort",
        "Bellagio Casino Hotel",
        "Macau Gaming Ventures",
    ],
}

TOR_EXIT_IPS = [
    "185.220.101.5",
    "185.220.101.7",
    "198.51.100.84",
    "45.154.255.88",
    "193.189.100.12",
]


def get_clean_customers() -> list[BankingCustomerRecord]:
    """Retrieve verified everyday retail banking customers."""
    customers = bank_db.list_all_customers()
    return [
        c
        for c in customers
        if not c.profile.user_id.startswith("USR_VICTIM")
        and not c.profile.user_id.startswith("USR_SMURF")
    ]


def get_victim_customers() -> list[BankingCustomerRecord]:
    """Retrieve dedicated victim accounts targeted for account takeover attacks."""
    return [c for c in bank_db.list_all_customers() if c.profile.user_id.startswith("USR_VICTIM")]


def get_smurf_customers() -> list[BankingCustomerRecord]:
    """Retrieve dedicated mule accounts targeted for BSA structuring bursts."""
    return [c for c in bank_db.list_all_customers() if c.profile.user_id.startswith("USR_SMURF")]


class RealWorldTrafficEngine:
    """Enterprise-scale realistic financial transaction generator."""

    def __init__(
        self,
        target_url: str = "http://127.0.0.1:8080/v1/transactions:analyze?mode=sync",
        total_txs: int = 10000,
        delay_sec: float = 2.5,
        target_tps: float | None = None,
        session_tag: str | None = None,
    ) -> None:
        self.target_url = target_url
        self.total_txs = total_txs
        self.delay_sec = (1.0 / target_tps) if target_tps else delay_sec
        self.target_tps = target_tps if target_tps else (1.0 / self.delay_sec)
        # Session-unique 4-char hex tag to guarantee idempotency across multiple runs
        self.session_tag = session_tag or hex(int(time.time()))[4:].upper()
        self.running = True
        self.stats: dict[str, int] = {
            "total": 0,
            "allow": 0,
            "challenge_3ds": 0,
            "block_tx": 0,
            "lock_account": 0,
            "decline_locked": 0,
            "review": 0,
            "errors": 0,
        }

    def generate_single_transaction(self, seq: int) -> tuple[Transaction, str]:
        """Generate an authentic transaction according to real-world risk distributions.

        Distribution across 10,000 transactions:
        - 95.0% Organic Benign (clean accounts, fast-path triage, <20ms, $0 tokens)
        -  2.5% Tor / Impossible Travel Account Takeover (victim accounts, autonomous lockout)
        -  2.0% BSA Structuring / Smurfing Velocity (mule accounts, deterministic block)
        -  0.5% 3DS Step-Up Challenge (unrecognized new devices, out-of-band verification)

        Returns:
            Tuple of (Transaction, scenario_label)
        """
        rand_val = random.random()

        # 1. Tor Exit Node / Impossible Travel Account Takeover (2.5%)
        if rand_val < 0.025:
            victims = get_victim_customers()
            victim = random.choice(victims) if victims else bank_db.get_customer("USR_VICTIM01")
            victim_id = victim.profile.user_id if victim else "USR_VICTIM01"
            amount = round(random.uniform(3500.00, 14800.00), 2)
            ip = random.choice(TOR_EXIT_IPS)
            crypto_merchants = MERCHANTS[MerchantCategory.CRYPTOCURRENCY_BROKERAGE]
            foreign_cities = [
                ("Frankfurt", "DE", 50.1109, 8.6821),
                ("Amsterdam", "NL", 52.3676, 4.9041),
                ("Moscow", "RU", 55.7558, 37.6173),
                ("Zurich", "CH", 47.3769, 8.5417),
            ]
            city, country, lat, lon = random.choice(foreign_cities)
            tx = Transaction(
                tx_id=f"TX_ATO{self.session_tag}{seq:04d}",
                user_id=victim_id,
                timestamp=datetime.now(UTC),
                amount=Decimal(str(amount)),
                currency="USD",
                merchant=random.choice(crypto_merchants),
                merchant_category=MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
                channel=Channel.ECOMMERCE,
                device_id=f"DEV_UNRECOGNIZED_{random.randint(100, 999)}",
                ip_address=IPv4Address(ip),
                location=Location(
                    latitude=lat,
                    longitude=lon,
                    city=city,
                    country=country,
                ),
            )
            return tx, "ATO_IMPOSSIBLE_TRAVEL"

        # 2. BSA Smurfing Structuring Velocity (2.0%)
        if rand_val < 0.045:
            smurfs = get_smurf_customers()
            smurf = random.choice(smurfs) if smurfs else None
            smurf_id = smurf.profile.user_id if smurf else f"USR_SMURF{random.randint(1, 10):02d}"
            amount = round(random.uniform(9200.00, 9950.00), 2)
            remittance_merchants = MERCHANTS[MerchantCategory.MONEY_TRANSFER]
            tx = Transaction(
                tx_id=f"TX_SMURF{self.session_tag}{seq:04d}",
                user_id=smurf_id,
                timestamp=datetime.now(UTC),
                amount=Decimal(str(amount)),
                currency="USD",
                merchant=random.choice(remittance_merchants),
                merchant_category=MerchantCategory.MONEY_TRANSFER,
                channel=Channel.ECOMMERCE,
                device_id=f"DEV_PROXY_{random.randint(10, 99)}",
                ip_address=IPv4Address("198.51.100.84"),
                location=Location(
                    latitude=40.7128,
                    longitude=-74.0060,
                    city="New York",
                    country="US",
                ),
            )
            return tx, "BSA_STRUCTURING"

        # 3. 3DS Step-Up Challenge (0.5%)
        if rand_val < 0.050:
            clean_custs = get_clean_customers()
            cust = random.choice(clean_custs)
            amount = round(random.uniform(550.00, 1250.00), 2)
            electronics_merchants = MERCHANTS.get(
                MerchantCategory.ELECTRONICS, MERCHANTS[MerchantCategory.RETAIL]
            )
            merchant_name = random.choice(electronics_merchants)
            tx = Transaction(
                tx_id=f"TX_3DS{self.session_tag}{seq:04d}",
                user_id=cust.profile.user_id,
                timestamp=datetime.now(UTC),
                amount=Decimal(str(amount)),
                currency="USD",
                merchant=merchant_name,
                merchant_category=MerchantCategory.ELECTRONICS,
                channel=Channel.ECOMMERCE,
                device_id=f"DEV_NEW_IPHONE_{random.randint(100, 999)}",
                ip_address=IPv4Address(
                    f"172.56.{random.randint(10, 90)}.{random.randint(2, 250)}"
                ),
                location=Location(
                    latitude=cust.profile.home_latitude + random.uniform(-0.02, 0.02),
                    longitude=cust.profile.home_longitude + random.uniform(-0.02, 0.02),
                    city=cust.profile.city,
                    country="US",
                ),
            )
            return tx, "3DS_STEP_UP_CHALLENGE"

        # 4. Organic Benign Everyday Purchase (95.0%)
        clean_custs = get_clean_customers()
        cust = random.choice(clean_custs)
        # Select merchant category consistent with customer baseline
        known_cats = [
            MerchantCategory(c)
            for c in cust.baseline.known_categories
            if c in MerchantCategory._value2member_map_
        ]
        cat = random.choice(known_cats) if known_cats else MerchantCategory.GROCERY
        merchant_name = random.choice(MERCHANTS.get(cat, MERCHANTS[MerchantCategory.RETAIL]))
        # Gaussian sampling around baseline average and std
        base_amt = random.gauss(cust.baseline.avg_amount, cust.baseline.std_amount)
        amount = round(max(3.50, min(cust.baseline.p95_amount * 1.15, base_amt)), 2)

        # Residential IP from trusted subnet
        subnet = cust.devices[0].trusted_ip_subnet if cust.devices else "73.189.42.0/24"
        ip_prefix = subnet.rsplit(".", 1)[0]
        ip = f"{ip_prefix}.{random.randint(2, 250)}"
        device_id = (
            cust.devices[0].device_id
            if cust.devices
            else f"DEV_{cust.profile.user_id}_PHONE"
        )

        tx = Transaction(
            tx_id=f"TX_LIVE{self.session_tag}{seq:04d}",
            user_id=cust.profile.user_id,
            timestamp=datetime.now(UTC),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant=merchant_name,
            merchant_category=cat,
            channel=random.choice([Channel.CARD_PRESENT, Channel.ECOMMERCE]),
            device_id=device_id,
            ip_address=IPv4Address(ip),
            location=Location(
                latitude=cust.profile.home_latitude + random.uniform(-0.008, 0.008),
                longitude=cust.profile.home_longitude + random.uniform(-0.008, 0.008),
                city=cust.profile.city,
                country="US",
            ),
        )
        return tx, "ORGANIC_BENIGN"

    def export_dataset_json(
        self, output_path: str = "data/eval/golden_10k_realworld.json"
    ) -> dict[str, Any]:
        """Export all 10,000 transactions as an offline evaluation dataset."""
        print(
            f"[*] Generating {self.total_txs} real-world transactions for offline evaluation...",
            flush=True,
        )
        dataset: list[dict[str, Any]] = []

        scenario_counts: dict[str, int] = {
            "ORGANIC_BENIGN": 0,
            "ATO_IMPOSSIBLE_TRAVEL": 0,
            "BSA_STRUCTURING": 0,
            "3DS_STEP_UP_CHALLENGE": 0,
        }

        for i in range(1, self.total_txs + 1):
            tx, scenario = self.generate_single_transaction(i)
            scenario_counts[scenario] += 1
            dataset.append({
                "case_id": tx.tx_id,
                "scenario": scenario,
                "is_fraud": scenario != "ORGANIC_BENIGN",
                "expected_decision": (
                    "ALLOW"
                    if scenario == "ORGANIC_BENIGN"
                    else "LOCK_ACCOUNT"
                    if scenario == "ATO_IMPOSSIBLE_TRAVEL"
                    else "BLOCK_TX"
                    if scenario == "BSA_STRUCTURING"
                    else "CHALLENGE_3DS"
                ),
                "transaction": tx.model_dump(mode="json"),
            })

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(dataset, f, indent=2)

        file_bytes = out.stat().st_size
        sha256 = hashlib.sha256(out.read_bytes()).hexdigest()

        summary = {
            "total_transactions": len(dataset),
            "scenarios": scenario_counts,
            "output_file": str(out),
            "file_size_mb": round(file_bytes / (1024 * 1024), 2),
            "sha256_checksum": sha256,
        }

        mb_size = summary["file_size_mb"]
        print(
            f"[OK] Exported {len(dataset)} transactions to {output_path} ({mb_size} MB)",
            flush=True,
        )
        print(f"     Breakdown: {scenario_counts}", flush=True)
        return summary

    def _process_response(
        self, seq: int, tx: Transaction, resp_data: dict[str, Any], latency_ms: int
    ) -> None:
        """Process API Gateway decision, update bank_db records, and log telemetry."""
        decision = resp_data.get("decision", "UNKNOWN")
        score = resp_data.get("threat_score", 0)
        self.stats["total"] += 1

        cust = bank_db.get_customer(tx.user_id)
        cust_name = cust.profile.full_name if cust else tx.user_id
        card_str = (
            f"Visa ..{cust.cards[0].masked_pan[-4:]}"
            if (cust and cust.cards)
            else "N/A"
        )
        bal_str = (
            f"${cust.accounts[0].current_balance:,.0f}"
            if (cust and cust.accounts)
            else "N/A"
        )

        protection_note = ""
        if decision == "ALLOW":
            self.stats["allow"] += 1
            if cust:
                bank_db.debit_account(tx.user_id, tx.amount)
                rem = f"${cust.accounts[0].current_balance:,.0f}"
                protection_note = f"Debited -> Rem: {rem} (Fast-Path)"
            else:
                protection_note = "Fast-Path Clean"
        elif decision == "CHALLENGE_3DS":
            self.stats["challenge_3ds"] += 1
            if cust:
                bank_db.challenge_card(tx.user_id)
            phone = cust.profile.phone if cust else "+1-555-0199"
            protection_note = f"[3DS ALERT] SMS OTP Dispatched to {phone}"
        elif decision == "BLOCK_TX":
            self.stats["block_tx"] += 1
            protection_note = "[BSA ALERT] Blocked Structuring (<$10k CTR)"
        elif decision == "LOCK_ACCOUNT":
            self.stats["lock_account"] += 1
            if cust:
                bank_db.lock_account(tx.user_id)
                prot = f"${cust.accounts[0].current_balance:,.0f}"
                protection_note = f"[CONTAINMENT] DDA Frozen! {prot} Protected"
            else:
                protection_note = "[CONTAINMENT] Account Locked"
        elif decision in ("DECLINE_LOCKED", "CARD_SUSPENDED"):
            self.stats["decline_locked"] += 1
            protection_note = "[TIER 0 HOT-SHIELD] Inactive Card Declined (<1ms)"
        elif decision == "REVIEW":
            self.stats["review"] += 1
            protection_note = "[ANALYST REVIEW] Queued for Deep Inspection"

        ts = datetime.now(UTC).strftime("%H:%M:%S")
        merch = tx.merchant[:20]
        amt = float(tx.amount)
        print(
            f"[{ts}] #{seq:04d} [{decision:<14}] {tx.tx_id} | "
            f"{cust_name} ({card_str}) | ${amt:,.2f} at {merch} | "
            f"Bal: {bal_str} | Score: {score:3d} | {latency_ms:3d}ms | {protection_note}",
            flush=True,
        )

    def _print_summary(self) -> None:
        """Print simulation summary statistics."""
        print("\n==================================================================", flush=True)
        print("                 Live Simulation Stream Completed                 ", flush=True)
        total = self.stats["total"]
        allow = self.stats["allow"]
        c3ds = self.stats["challenge_3ds"]
        block = self.stats["block_tx"]
        lock = self.stats["lock_account"]
        decl = self.stats["decline_locked"]
        review = self.stats["review"]
        errs = self.stats["errors"]
        print(
            f"Total Processed: {total} | ALLOW: {allow} | CHALLENGE_3DS: {c3ds} | "
            f"BLOCK: {block} | LOCK: {lock} | DECLINE_LOCKED: {decl} | "
            f"REVIEW: {review} | ERRORS: {errs}",
            flush=True,
        )
        print("==================================================================", flush=True)

    async def stream_live(self) -> None:
        """Stream real-world transactions continuously with natural human observation pacing."""
        cust_cnt = len(bank_db.list_all_customers())
        print("==================================================================", flush=True)
        print("     Aegis Real-World Banking Traffic Streamer (10,000 Tx)       ", flush=True)
        print("==================================================================", flush=True)
        print(f"[*] Target Endpoint:   {self.target_url}", flush=True)
        print(f"[*] Total Target:      {self.total_txs} transactions", flush=True)
        print(
            f"[*] Observation Pace:  ~{self.delay_sec:.1f}s interval between transactions",
            flush=True,
        )
        print(f"[*] Banking Personas:  {cust_cnt} authentic BFSI customer accounts", flush=True)
        print(
            "[*] Traffic Mix:       95% Benign, 2.5% Tor ATO, 2.0% Structuring, 0.5% 3DS",
            flush=True,
        )
        print("[*] SOC Dashboard:     http://localhost:5173", flush=True)
        print("==================================================================\n", flush=True)

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                for seq in range(1, self.total_txs + 1):
                    if not self.running:
                        break

                    tx, _scenario = self.generate_single_transaction(seq)
                    payload = tx.model_dump(mode="json")

                    start = time.perf_counter()
                    try:
                        resp = await client.post(self.target_url, json=payload)
                        latency_ms = int((time.perf_counter() - start) * 1000)

                        if resp.status_code == 200:
                            self._process_response(seq, tx, resp.json(), latency_ms)
                        else:
                            self.stats["errors"] += 1
                            print(
                                f"[!] HTTP {resp.status_code} for {tx.tx_id}: {resp.text[:80]}",
                                flush=True,
                            )

                    except Exception as ex:
                        self.stats["errors"] += 1
                        print(f"[!] Request error on {tx.tx_id}: {ex}", flush=True)

                    # Human observation interval: clamped Poisson jitter between 2.0s and 3.5s
                    jitter = random.expovariate(1.0 / self.delay_sec)
                    clamped_delay = max(2.0, min(3.5, jitter))
                    await asyncio.sleep(clamped_delay)

        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n[*] Live streaming paused by analyst.", flush=True)
        finally:
            self._print_summary()


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Aegis 10,000 Real-World Traffic Generator")
    parser.add_argument(
        "--count", type=int, default=10000, help="Total transactions to generate (default: 10000)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.5,
        help="Target delay in seconds between transactions (default: 2.5s)",
    )
    parser.add_argument(
        "--tps",
        type=float,
        default=None,
        help="Target transactions per second (reciprocal of delay, optional)",
    )
    parser.add_argument(
        "--mode",
        choices=["stream", "export", "both"],
        default="both",
        help="Execution mode: 'stream' (live API), 'export' (JSON file), or 'both'",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/eval/golden_10k_realworld.json",
        help="Output path for evaluation dataset export",
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8080/v1/transactions:analyze?mode=sync",
        help="Target API Gateway ingestion endpoint",
    )

    args = parser.parse_args()

    engine = RealWorldTrafficEngine(
        target_url=args.url,
        total_txs=args.count,
        delay_sec=args.delay,
        target_tps=args.tps,
    )

    try:
        if args.mode in ("export", "both"):
            engine.export_dataset_json(output_path=args.output)

        if args.mode in ("stream", "both"):
            asyncio.run(engine.stream_live())
    except KeyboardInterrupt:
        print("\n[*] Exiting simulation.", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()
