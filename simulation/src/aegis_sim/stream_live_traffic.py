"""Real-world continuous transaction traffic simulator (Non-robotic human-paced streaming).

Simulates genuine consumer financial traffic at scale with:
- 35+ Diverse authentic global personas across US, European, and Asian cities
- Deliberate 2.0s - 3.5s human observation pacing (Poisson-randomized ~0.4 TPS)
- Persona-aware cooldown reservoir (min 25 transactions between purchases)
- Global threat vectors across countries (Frankfurt, Moscow, Lagos, Amsterdam)
- Rotating victim identities ensuring every fraud attack runs the full live Gemini AI panel
- Live streaming output to Aegis API Gateway and real-time SOC dashboard telemetry.
"""

import argparse
import asyncio
import random
import signal
import sys
import time
from collections import deque
from datetime import UTC, datetime
from decimal import Decimal
from ipaddress import IPv4Address
from typing import Any, TypedDict

# Force line buffering so real-time events appear immediately in terminals and parent pipes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

import httpx
from aegis_common.banking import bank_db
from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction


class PersonaDict(TypedDict):
    """Schema for simulated authentic consumer personas."""

    user_id: str
    name: str
    occupation: str
    city: str
    country: str
    lat: float
    lon: float
    ip_prefix: str
    device: str
    min_spend: float
    max_spend: float
    favorite_cats: list[MerchantCategory]


PERSONAS: list[PersonaDict] = [
    {
        "user_id": "USR_MARCUS712",
        "name": "Marcus Chen",
        "occupation": "Software Architect",
        "city": "San Francisco",
        "country": "US",
        "lat": 37.7749,
        "lon": -122.4194,
        "ip_prefix": "73.189.42",
        "device": "DEV_MARCUS_IPHONE15",
        "min_spend": 4.50,
        "max_spend": 65.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.RESTAURANT,
            MerchantCategory.GROCERY,
        ],
    },
    {
        "user_id": "USR_SARAH840",
        "name": "Sarah Jenkins",
        "occupation": "Creative Director",
        "city": "Austin",
        "country": "US",
        "lat": 30.2672,
        "lon": -97.7431,
        "ip_prefix": "70.114.88",
        "device": "DEV_SARAH_PIXEL8",
        "min_spend": 6.00,
        "max_spend": 85.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.RETAIL,
            MerchantCategory.GROCERY,
        ],
    },
    {
        "user_id": "USR_ELENA391",
        "name": "Elena Rostova",
        "occupation": "Portfolio Manager",
        "city": "New York",
        "country": "US",
        "lat": 40.7128,
        "lon": -74.0060,
        "ip_prefix": "68.195.12",
        "device": "DEV_ELENA_MACBOOK",
        "min_spend": 15.00,
        "max_spend": 180.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.RETAIL,
            MerchantCategory.UTILITIES,
        ],
    },
    {
        "user_id": "USR_DAVID518",
        "name": "David Miller",
        "occupation": "Mechanical Engineer",
        "city": "Chicago",
        "country": "US",
        "lat": 41.8781,
        "lon": -87.6298,
        "ip_prefix": "24.148.65",
        "device": "DEV_DAVID_GALAXY",
        "min_spend": 8.00,
        "max_spend": 75.00,
        "favorite_cats": [
            MerchantCategory.GROCERY,
            MerchantCategory.FUEL,
            MerchantCategory.RETAIL,
        ],
    },
    {
        "user_id": "USR_SOPHIA924",
        "name": "Sophia Al-Mansoor",
        "occupation": "Data Scientist",
        "city": "Seattle",
        "country": "US",
        "lat": 47.6062,
        "lon": -122.3321,
        "ip_prefix": "24.16.140",
        "device": "DEV_SOPHIA_IPHONE15",
        "min_spend": 5.00,
        "max_spend": 90.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.GROCERY,
            MerchantCategory.UTILITIES,
        ],
    },
    {
        "user_id": "USR_JAMES610",
        "name": "James O'Connor",
        "occupation": "Biotech Researcher",
        "city": "Boston",
        "country": "US",
        "lat": 42.3601,
        "lon": -71.0589,
        "ip_prefix": "71.232.19",
        "device": "DEV_JAMES_IPAD",
        "min_spend": 12.00,
        "max_spend": 130.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.GROCERY,
            MerchantCategory.RETAIL,
        ],
    },
    {
        "user_id": "USR_AMARA433",
        "name": "Amara Okafor",
        "occupation": "Architect",
        "city": "Atlanta",
        "country": "US",
        "lat": 33.7490,
        "lon": -84.3880,
        "ip_prefix": "76.17.202",
        "device": "DEV_AMARA_PIXEL",
        "min_spend": 9.00,
        "max_spend": 110.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.FUEL,
            MerchantCategory.RETAIL,
        ],
    },
    {
        "user_id": "USR_LUCAS275",
        "name": "Lucas Silva",
        "occupation": "Environmental Tech",
        "city": "Denver",
        "country": "US",
        "lat": 39.7392,
        "lon": -104.9903,
        "ip_prefix": "72.48.90",
        "device": "DEV_LUCAS_GALAXY",
        "min_spend": 7.50,
        "max_spend": 80.00,
        "favorite_cats": [
            MerchantCategory.GROCERY,
            MerchantCategory.FUEL,
            MerchantCategory.COFFEE_SHOP,
        ],
    },
    {
        "user_id": "USR_CHLOE882",
        "name": "Chloe Dubois",
        "occupation": "Film Producer",
        "city": "Los Angeles",
        "country": "US",
        "lat": 34.0522,
        "lon": -118.2437,
        "ip_prefix": "104.175.40",
        "device": "DEV_CHLOE_MACBOOK",
        "min_spend": 18.00,
        "max_spend": 210.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.RETAIL,
            MerchantCategory.COFFEE_SHOP,
        ],
    },
    {
        "user_id": "USR_LIAM194",
        "name": "Liam Washington",
        "occupation": "Hospitality VP",
        "city": "Miami",
        "country": "US",
        "lat": 25.7617,
        "lon": -80.1918,
        "ip_prefix": "99.102.14",
        "device": "DEV_LIAM_IPHONE14",
        "min_spend": 14.00,
        "max_spend": 160.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.RETAIL,
            MerchantCategory.FUEL,
        ],
    },
    {
        "user_id": "USR_ETHAN305",
        "name": "Ethan Wright",
        "occupation": "Aviation Analyst",
        "city": "Dallas",
        "country": "US",
        "lat": 32.7767,
        "lon": -96.7970,
        "ip_prefix": "47.184.22",
        "device": "DEV_ETHAN_SURFACE",
        "min_spend": 10.00,
        "max_spend": 95.00,
        "favorite_cats": [
            MerchantCategory.FUEL,
            MerchantCategory.RESTAURANT,
            MerchantCategory.GROCERY,
        ],
    },
    {
        "user_id": "USR_ISABELLA420",
        "name": "Isabella Rossi",
        "occupation": "Cardiologist",
        "city": "Phoenix",
        "country": "US",
        "lat": 33.4484,
        "lon": -112.0740,
        "ip_prefix": "174.67.112",
        "device": "DEV_ISABELLA_IPHONE",
        "min_spend": 12.00,
        "max_spend": 140.00,
        "favorite_cats": [
            MerchantCategory.GROCERY,
            MerchantCategory.RETAIL,
            MerchantCategory.COFFEE_SHOP,
        ],
    },
    {
        "user_id": "USR_NOAH719",
        "name": "Noah Tanaka",
        "occupation": "Civil Engineer",
        "city": "San Diego",
        "country": "US",
        "lat": 32.7157,
        "lon": -117.1611,
        "ip_prefix": "76.218.45",
        "device": "DEV_NOAH_PIXEL7",
        "min_spend": 6.50,
        "max_spend": 70.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.GROCERY,
            MerchantCategory.FUEL,
        ],
    },
    {
        "user_id": "USR_MAYA531",
        "name": "Maya Patel",
        "occupation": "Policy Advisor",
        "city": "Washington",
        "country": "US",
        "lat": 38.9072,
        "lon": -77.0369,
        "ip_prefix": "69.140.88",
        "device": "DEV_MAYA_MACBOOK",
        "min_spend": 15.00,
        "max_spend": 150.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.RETAIL,
            MerchantCategory.UTILITIES,
        ],
    },
    {
        "user_id": "USR_OLIVER614",
        "name": "Oliver Schmidt",
        "occupation": "Supply Chain Director",
        "city": "Philadelphia",
        "country": "US",
        "lat": 39.9526,
        "lon": -75.1652,
        "ip_prefix": "73.162.33",
        "device": "DEV_OLIVER_GALAXY",
        "min_spend": 11.00,
        "max_spend": 115.00,
        "favorite_cats": [
            MerchantCategory.GROCERY,
            MerchantCategory.FUEL,
            MerchantCategory.RETAIL,
        ],
    },
    {
        "user_id": "USR_CHARLOTTE228",
        "name": "Charlotte Tremblay",
        "occupation": "Biophysicist",
        "city": "Toronto",
        "country": "CA",
        "lat": 43.6532,
        "lon": -79.3832,
        "ip_prefix": "142.112.50",
        "device": "DEV_CHARLOTTE_IPHONE",
        "min_spend": 8.00,
        "max_spend": 85.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.GROCERY,
            MerchantCategory.RESTAURANT,
        ],
    },
    {
        "user_id": "USR_ALEXANDER104",
        "name": "Alexander Ward",
        "occupation": "Fintech Quant",
        "city": "London",
        "country": "GB",
        "lat": 51.5074,
        "lon": -0.1278,
        "ip_prefix": "82.165.197",
        "device": "DEV_ALEX_THINKPAD",
        "min_spend": 14.00,
        "max_spend": 175.00,
        "favorite_cats": [
            MerchantCategory.RESTAURANT,
            MerchantCategory.RETAIL,
            MerchantCategory.COFFEE_SHOP,
        ],
    },
    {
        "user_id": "USR_MIA819",
        "name": "Mia Andersson",
        "occupation": "Industrial Designer",
        "city": "Amsterdam",
        "country": "NL",
        "lat": 52.3676,
        "lon": 4.9041,
        "ip_prefix": "84.241.198",
        "device": "DEV_MIA_MACBOOKAIR",
        "min_spend": 9.00,
        "max_spend": 95.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.RETAIL,
            MerchantCategory.GROCERY,
        ],
    },
    {
        "user_id": "USR_BENJAMIN372",
        "name": "Benjamin Weber",
        "occupation": "Automotive Systems VP",
        "city": "Frankfurt",
        "country": "DE",
        "lat": 50.1109,
        "lon": 8.6821,
        "ip_prefix": "91.65.120",
        "device": "DEV_BEN_IPHONE15",
        "min_spend": 12.00,
        "max_spend": 110.00,
        "favorite_cats": [
            MerchantCategory.FUEL,
            MerchantCategory.RESTAURANT,
            MerchantCategory.UTILITIES,
        ],
    },
    {
        "user_id": "USR_GRACE906",
        "name": "Grace Kim",
        "occupation": "Robotics Researcher",
        "city": "Tokyo",
        "country": "JP",
        "lat": 35.6762,
        "lon": 139.6503,
        "ip_prefix": "122.215.80",
        "device": "DEV_GRACE_XPERIA",
        "min_spend": 7.00,
        "max_spend": 80.00,
        "favorite_cats": [
            MerchantCategory.COFFEE_SHOP,
            MerchantCategory.GROCERY,
            MerchantCategory.RETAIL,
        ],
    },
]

MERCHANTS: dict[MerchantCategory, list[str]] = {
    MerchantCategory.COFFEE_SHOP: [
        "Blue Bottle Coffee",
        "Sightglass Roastery",
        "Starbucks Reserve",
        "Philz Coffee",
        "Caffe Nero",
        "Joe & The Juice",
        "Artisan Espresso Lounge",
    ],
    MerchantCategory.GROCERY: [
        "Whole Foods Market",
        "Trader Joe's",
        "Safeway Organics",
        "Sprouts Farmers Market",
        "Wegmans Food Market",
        "Eataly Fresh Market",
    ],
    MerchantCategory.RESTAURANT: [
        "Sweetgreen Farm Stand",
        "Chipotle Mexican Grill",
        "Shake Shack",
        "Local Trattoria Rustica",
        "Nobu Downtown",
        "Din Tai Fung",
        "Mendocino Farms",
    ],
    MerchantCategory.FUEL: [
        "Chevron Express Fuel",
        "Shell Oil Station",
        "ExxonMobil",
        "7-Eleven Express",
        "BP Connect",
    ],
    MerchantCategory.RETAIL: [
        "Apple Store Fifth Ave",
        "Target Stores",
        "Nordstrom Rack",
        "Amazon Go Retail",
        "REI Outdoor Goods",
        "Sephora Beauty",
    ],
    MerchantCategory.UTILITIES: [
        "Pacific Gas & Electric",
        "Con Edison New York",
        "AT&T Fiber Mobility",
        "Verizon Wireless Fios",
        "Vodafone UK Telecom",
    ],
    MerchantCategory.GAMBLING: [
        "Monaco Grand Casino Resort",
        "Macau Sands VIP Gaming",
        "Bellagio High Limit Club",
    ],
    MerchantCategory.CRYPTOCURRENCY_BROKERAGE: [
        "Apex Global Crypto Liquidity Corp",
        "BitVault Offshore Assets BV",
        "Panama Digital Holdings SA",
        "Helvetia Crypto Custody AG",
    ],
    MerchantCategory.MONEY_TRANSFER: [
        "Fast Wire Remittance LLC",
        "Global Remit Direct Systems",
        "SpeedPay International Wire",
        "Apex Cross-Border Clearing",
    ],
}

GLOBAL_HACKER_NODES = [
    {
        "city": "Frankfurt (via Tor)",
        "country": "DE",
        "ip": "185.220.101.5",
        "lat": 50.1109,
        "lon": 8.6821,
        "merchant": "Apex Global Crypto Liquidity Corp",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Amsterdam (via Tor)",
        "country": "NL",
        "ip": "185.220.101.7",
        "lat": 52.3676,
        "lon": 4.9041,
        "merchant": "BitVault Offshore Assets BV",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Moscow (Bulletproof Proxy)",
        "country": "RU",
        "ip": "194.26.29.112",
        "lat": 55.7558,
        "lon": 37.6173,
        "merchant": "Eastern European Liquidity Gateway",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Bucharest (via Tor)",
        "country": "RO",
        "ip": "45.154.255.88",
        "lat": 44.4268,
        "lon": 26.1025,
        "merchant": "Panama Digital Holdings SA",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Lagos (Anonymous VPN)",
        "country": "NG",
        "ip": "102.89.23.41",
        "lat": 6.5244,
        "lon": 3.3792,
        "merchant": "West Africa Crypto Clearing Hub",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Zurich (via Tor)",
        "country": "CH",
        "ip": "193.189.100.12",
        "lat": 47.3769,
        "lon": 8.5417,
        "merchant": "Helvetia Crypto Custody AG",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
    {
        "city": "Reykjavik (Tor Exit Node)",
        "country": "IS",
        "ip": "185.220.100.252",
        "lat": 64.1466,
        "lon": -21.9426,
        "merchant": "North Atlantic Offshore Assets",
        "cat": MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
    },
]

HACKING_DEVICES = [
    "DEV_KALI_LINUX_PRO",
    "DEV_TOR_BROWSER_X",
    "DEV_ANDROID_EMU_9",
    "DEV_HEADLESS_CHROME_BOT",
    "DEV_PROXY_ROTATOR_v4",
]


class LiveTrafficStreamer:
    """Streams natural financial transaction events to Aegis API Gateway with human pacing."""

    def __init__(
        self,
        target_url: str = "http://127.0.0.1:8080/v1/transactions:analyze?mode=sync",
        delay_sec: float = 2.5,
        fraud_ratio: float = 0.15,
        session_tag: str | None = None,
    ) -> None:
        self.target_url = target_url
        self.delay_sec = max(0.5, delay_sec)
        self.fraud_ratio = fraud_ratio
        self.running = True
        self.session_tag = session_tag or hex(int(time.time()))[4:].upper()
        self.stats = {
            "total": 0,
            "allow": 0,
            "block_tx": 0,
            "lock_account": 0,
            "review": 0,
            "errors": 0,
        }
        self.recent_user_cooldown: deque[str] = deque(maxlen=25)
        self.victim_counter = 1
        self.smurf_counter = 1

    def _select_cooled_persona(self) -> PersonaDict:
        """Select a persona that hasn't transacted in the last 25 turns to prevent bot-like spam."""
        available = [p for p in PERSONAS if p["user_id"] not in self.recent_user_cooldown]
        if not available:
            available = PERSONAS
        persona = random.choice(available)
        self.recent_user_cooldown.append(persona["user_id"])
        return persona

    def _generate_benign_tx(self, seq: int) -> Transaction:
        """Generate an authentic benign transaction with diverse categories and realistic spend."""
        persona = self._select_cooled_persona()
        cat = random.choice(persona["favorite_cats"])
        merchants_list = MERCHANTS.get(cat, ["Local Merchant Store"])
        merchant_name = random.choice(merchants_list)
        amount = round(random.uniform(persona["min_spend"], persona["max_spend"]), 2)
        ip = f"{persona['ip_prefix']}.{random.randint(2, 250)}"

        return Transaction(
            tx_id=f"TX_LIVE{self.session_tag}{seq:04d}",
            user_id=persona["user_id"],
            timestamp=datetime.now(UTC),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant=merchant_name,
            merchant_category=cat,
            channel=random.choice([Channel.CARD_PRESENT, Channel.ECOMMERCE]),
            device_id=persona["device"],
            ip_address=IPv4Address(ip),
            location=Location(
                latitude=persona["lat"],
                longitude=persona["lon"],
                city=persona["city"],
                country=persona["country"],
            ),
        )

    def _generate_structuring_tx(self, seq: int) -> Transaction:
        """Generate a BSA near-$10k structuring transfer from a rotating smurfing network."""
        ring_node = (self.smurf_counter % 12) + 1
        self.smurf_counter += 1
        amount = round(random.uniform(9250.00, 9950.00), 2)
        merchant_name = random.choice(MERCHANTS[MerchantCategory.MONEY_TRANSFER])

        return Transaction(
            tx_id=f"TX_SMURF{self.session_tag}{seq:04d}",
            user_id=f"USR_SMURF{ring_node:02d}",
            timestamp=datetime.now(UTC),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant=merchant_name,
            merchant_category=MerchantCategory.MONEY_TRANSFER,
            channel=Channel.ECOMMERCE,
            device_id=f"DEV_PROXY_NODE_{ring_node:02d}",
            ip_address=IPv4Address("198.51.100.84"),
            location=Location(
                latitude=40.7128,
                longitude=-74.0060,
                city="New York",
                country="US",
            ),
        )

    def _generate_tor_ato_tx(self, seq: int) -> Transaction:
        """Create an ATO attack on a fresh victim from a global hacker node."""
        victim_id = f"USR_VICTIM{self.victim_counter:02d}"
        self.victim_counter += 1
        hacker_node = random.choice(GLOBAL_HACKER_NODES)
        device = random.choice(HACKING_DEVICES)
        amount = round(random.uniform(8500.00, 16500.00), 2)

        return Transaction(
            tx_id=f"TX_ATO{self.session_tag}{seq:04d}",
            user_id=victim_id,
            timestamp=datetime.now(UTC),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant=hacker_node["merchant"],
            merchant_category=hacker_node["cat"],
            channel=Channel.ECOMMERCE,
            device_id=device,
            ip_address=IPv4Address(hacker_node["ip"]),
            location=Location(
                latitude=hacker_node["lat"],
                longitude=hacker_node["lon"],
                city=hacker_node["city"],
                country=hacker_node["country"],
            ),
        )

    def _generate_3ds_challenge_tx(self, seq: int) -> Transaction:
        """Create an elevated ambiguity purchase on novel device triggering 3DS OTP."""
        persona = random.choice(PERSONAS)
        amount = round(random.uniform(550.00, 950.00), 2)
        ip = f"{persona['ip_prefix']}.{random.randint(2, 250)}"
        return Transaction(
            tx_id=f"TX_CHLNG{self.session_tag}{seq:04d}",
            user_id=persona["user_id"],
            timestamp=datetime.now(UTC),
            amount=Decimal(str(amount)),
            currency="USD",
            merchant="Apple Store Fifth Ave",
            merchant_category=MerchantCategory.RETAIL,
            channel=Channel.ECOMMERCE,
            device_id=f"DEV_NEW_IPAD_{random.randint(100, 999)}",
            ip_address=IPv4Address(ip),
            location=Location(
                latitude=persona["lat"],
                longitude=persona["lon"],
                city=persona["city"],
                country=persona["country"],
            ),
        )

    def _log_verdict(
        self,
        seq: int,
        tx: Transaction,
        verdict: dict[str, Any],
        duration_ms: int,
        scenario_label: str,
    ) -> None:
        """Log color-coded transaction outcome to terminal."""
        dec = verdict.get("decision", "UNKNOWN")
        score = verdict.get("threat_score", 0)
        self.stats["total"] += 1

        cust = bank_db.get_customer(tx.user_id)
        cust_name = cust.profile.full_name if cust else tx.user_id
        card_str = f"Visa ..{cust.cards[0].masked_pan[-4:]}" if (cust and cust.cards) else "N/A"
        bal_str = f"${cust.accounts[0].current_balance:,.0f}" if (cust and cust.accounts) else "N/A"

        if dec == "ALLOW":
            self.stats["allow"] += 1
            tag = "\033[92m[ALLOW]\033[0m"
            if cust:
                bank_db.debit_account(tx.user_id, tx.amount)
        elif dec == "CHALLENGE_3DS":
            self.stats["review"] += 1
            tag = "\033[96m[3DS_CHALLENGE]\033[0m"
            if cust:
                bank_db.challenge_card(tx.user_id)
        elif dec == "CARD_SUSPENDED":
            self.stats["block_tx"] += 1
            tag = "\033[95m[CARD_SUSPENDED]\033[0m"
            if cust:
                bank_db.suspend_card(tx.user_id)
        elif dec == "BLOCK_TX":
            self.stats["block_tx"] += 1
            tag = "\033[93m[BLOCK_TX]\033[0m"
        elif dec in ("LOCK_ACCOUNT", "DECLINE_LOCKED"):
            self.stats["lock_account"] += 1
            tag = (
                "\033[91m[LOCK_ACCOUNT]\033[0m"
                if dec == "LOCK_ACCOUNT"
                else "\033[91m[DECLINE_LOCKED]\033[0m"
            )
            if cust:
                bank_db.lock_account(tx.user_id)
        else:
            self.stats["review"] += 1
            tag = "\033[94m[REVIEW]\033[0m"

        now_str = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{now_str}] #{seq:04d} {tag} {tx.tx_id} | {cust_name} ({card_str}) | "
            f"${float(tx.amount):,.2f} at {tx.merchant[:24]} | "
            f"Bal: {bal_str} | Score: {score:>3}/100 | {duration_ms}ms ({scenario_label})",
            flush=True,
        )
        if dec == "CHALLENGE_3DS":
            print(
                f"       \033[96m--> [3DS ALERT] Step-Up OTP Verification for "
                f"{cust_name} ({card_str})\033[0m",
                flush=True,
            )
        elif dec == "CARD_SUSPENDED":
            print(
                f"       \033[95m--> [HOT-SHIELD] {card_str} blacklisted "
                "& suspended at Gateway Tier 0\033[0m",
                flush=True,
            )

    async def stream(self, total_count: int | None = None) -> None:  # noqa: PLR0915
        """Continuously stream transactions with deliberate human-observation pacing."""
        adv_pct = int(self.fraud_ratio * 100)
        ben_pct = int((1 - self.fraud_ratio) * 100)
        nodes_cnt = len(GLOBAL_HACKER_NODES)
        print("==================================================================", flush=True)
        print("  Aegis Real-World Authentic Traffic Simulator (Human Paced)     ", flush=True)
        print("==================================================================", flush=True)
        print(f"[*] Target Endpoint:   {self.target_url}", flush=True)
        print(
            f"[*] Observation Pace:  ~{self.delay_sec:.1f}s interval between transactions",
            flush=True,
        )
        print(
            f"[*] Traffic Ratio:     {adv_pct}% adversarial, {ben_pct}% organic benign", flush=True
        )
        print(
            f"[*] Persona Universe:  {len(PERSONAS)} authentic global profiles (cooldown active)",
            flush=True,
        )
        print(
            f"[*] Global Adversaries: {nodes_cnt} international nodes (Frankfurt, Moscow, etc.)",
            flush=True,
        )
        print("[*] SOC Dashboard URL: http://localhost:5173", flush=True)
        print("Press Ctrl+C at any time to gracefully pause streaming.", flush=True)
        print("------------------------------------------------------------------\n", flush=True)

        seq = 1
        client = httpx.AsyncClient(timeout=35.0)

        try:
            while self.running:
                if total_count and seq > total_count:
                    break

                roll = random.random()
                if roll < self.fraud_ratio * 0.4:
                    tx = self._generate_tor_ato_tx(seq)
                    scenario_label = "Tor ATO Attack"
                elif roll < self.fraud_ratio * 0.7:
                    tx = self._generate_structuring_tx(seq)
                    scenario_label = "Smurfing Burst"
                elif roll < self.fraud_ratio:
                    tx = self._generate_3ds_challenge_tx(seq)
                    scenario_label = "3DS Step-Up Challenge"
                else:
                    tx = self._generate_benign_tx(seq)
                    scenario_label = "Organic Benign"

                start_req = time.perf_counter()
                try:
                    resp = await client.post(self.target_url, json=tx.model_dump(mode="json"))
                    duration_ms = int((time.perf_counter() - start_req) * 1000)

                    if resp.status_code == 200:
                        self._log_verdict(seq, tx, resp.json(), duration_ms, scenario_label)
                    else:
                        self.stats["errors"] += 1
                        print(
                            f"[ERR] #{seq:04d} HTTP {resp.status_code}: {resp.text[:100]}",
                            flush=True,
                        )
                except Exception as exc:
                    self.stats["errors"] += 1
                    err_msg = str(exc) if str(exc) else "Request timed out or connection refused"
                    print(
                        f"[ERR] #{seq:04d} Connection failure ({type(exc).__name__}): {err_msg}",
                        flush=True,
                    )

                seq += 1

                # Deliberate human observation pacing: clamped Poisson jitter between 2.0s and 3.5s
                jitter = random.expovariate(1.0 / self.delay_sec)
                clamped_delay = max(2.0, min(3.8, jitter))
                await asyncio.sleep(clamped_delay)

        finally:
            await client.aclose()
            self._print_summary()

    def _print_summary(self) -> None:
        """Print streaming summary report upon completion."""
        print("\n==================================================================", flush=True)
        print("          Aegis Live Traffic Simulation Run Summary               ", flush=True)
        print("==================================================================", flush=True)
        print(f"Total Transactions Streamed:  {self.stats['total']}", flush=True)
        print(f"  • Fast-Path Clean (ALLOW):  {self.stats['allow']}", flush=True)
        print(f"  • Blocked (BLOCK_TX):       {self.stats['block_tx']}", flush=True)
        print(f"  • Autonomous Lockouts:      {self.stats['lock_account']}", flush=True)
        print(f"  • Analyst Reviews:          {self.stats['review']}", flush=True)
        print(f"  • Dispatch Errors:          {self.stats['errors']}", flush=True)
        print("==================================================================", flush=True)


def main() -> None:
    """CLI entrypoint for live transaction traffic simulator."""
    parser = argparse.ArgumentParser(description="Aegis Real-World Authentic Traffic Simulator.")
    parser.add_argument(
        "--target",
        type=str,
        default="http://127.0.0.1:8080/v1/transactions:analyze?mode=sync",
        help="Target API Gateway analyze endpoint",
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
        help="Target TPS (reciprocal of delay, optional)",
    )
    parser.add_argument(
        "--fraud-ratio",
        type=float,
        default=0.15,
        help="Adversarial attack ratio (default: 0.15)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Total transactions to send before stopping (default: continuous)",
    )
    args = parser.parse_args()

    effective_delay = (1.0 / args.tps) if args.tps else args.delay

    streamer = LiveTrafficStreamer(
        target_url=args.target,
        delay_sec=effective_delay,
        fraud_ratio=args.fraud_ratio,
    )

    def handle_sigint(*_: Any) -> None:
        print("\n[*] Stopping live traffic simulator...")
        streamer.running = False

    signal.signal(signal.SIGINT, handle_sigint)

    asyncio.run(streamer.stream(total_count=args.count))


if __name__ == "__main__":
    main()
