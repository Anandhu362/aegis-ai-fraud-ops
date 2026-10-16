"""Central in-memory Banking Database repository with authentic US consumer personas."""

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from aegis_common.schemas.banking import (
    AccountStatus,
    AccountType,
    BankAccount,
    BankingCustomerRecord,
    CardBrand,
    CardStatus,
    CustomerProfile,
    CustomerRiskTier,
    DeviceFootprint,
    KycStatus,
    PaymentCard,
)
from aegis_common.schemas.enums import Channel
from aegis_common.schemas.features import UserBaseline

# Authentic US Metropolitan Regions Reference Data
METRO_REGIONS = {
    "SF": {
        "city": "San Francisco",
        "state": "CA",
        "country": "US",
        "lat": 37.7749,
        "lon": -122.4194,
        "ip_prefix": "73.189.42",
        "isp": "Comcast Cable Residential",
        "routing": "121000358",
    },
    "NYC": {
        "city": "New York",
        "state": "NY",
        "country": "US",
        "lat": 40.7128,
        "lon": -74.0060,
        "ip_prefix": "68.195.12",
        "isp": "Verizon Fios Residential",
        "routing": "021000021",
    },
    "ATX": {
        "city": "Austin",
        "state": "TX",
        "country": "US",
        "lat": 30.2672,
        "lon": -97.7431,
        "ip_prefix": "70.114.88",
        "isp": "AT&T Internet Services",
        "routing": "111000025",
    },
    "CHI": {
        "city": "Chicago",
        "state": "IL",
        "country": "US",
        "lat": 41.8781,
        "lon": -87.6298,
        "ip_prefix": "24.148.65",
        "isp": "Comcast Xfinity Chicago",
        "routing": "071000013",
    },
    "SEA": {
        "city": "Seattle",
        "state": "WA",
        "country": "US",
        "lat": 47.6062,
        "lon": -122.3321,
        "ip_prefix": "24.16.140",
        "isp": "CenturyLink Broadband",
        "routing": "125000024",
    },
    "BOS": {
        "city": "Boston",
        "state": "MA",
        "country": "US",
        "lat": 42.3601,
        "lon": -71.0589,
        "ip_prefix": "71.232.19",
        "isp": "Comcast Cable Boston",
        "routing": "011000015",
    },
    "ATL": {
        "city": "Atlanta",
        "state": "GA",
        "country": "US",
        "lat": 33.7490,
        "lon": -84.3880,
        "ip_prefix": "76.17.202",
        "isp": "Charter Spectrum Atlanta",
        "routing": "061000104",
    },
    "DEN": {
        "city": "Denver",
        "state": "CO",
        "country": "US",
        "lat": 39.7392,
        "lon": -104.9903,
        "ip_prefix": "72.48.90",
        "isp": "Comcast Cable Denver",
        "routing": "102000076",
    },
    "LAX": {
        "city": "Los Angeles",
        "state": "CA",
        "country": "US",
        "lat": 34.0522,
        "lon": -118.2437,
        "ip_prefix": "104.175.40",
        "isp": "Spectrum Residential LA",
        "routing": "122000496",
    },
    "MIA": {
        "city": "Miami",
        "state": "FL",
        "country": "US",
        "lat": 25.7617,
        "lon": -80.1918,
        "ip_prefix": "99.102.14",
        "isp": "AT&T U-verse Miami",
        "routing": "066004367",
    },
}


class BankingDatabase:
    """Thread-safe core banking repository providing authentic BFSI customer data."""

    _instance: "BankingDatabase | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "BankingDatabase":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize_records()
            return cls._instance

    def _initialize_records(self) -> None:
        """Seed the banking database with 50+ rich authentic customers and accounts."""
        self._customers: dict[str, BankingCustomerRecord] = {}
        self._cards_by_token: dict[str, PaymentCard] = {}
        self._cards_by_user: dict[str, list[PaymentCard]] = {}
        self._last_tx_by_user: dict[str, dict[str, Any]] = {}
        self._recent_txs_by_user: dict[str, list[tuple[datetime, float]]] = {}
        self._data_lock = threading.RLock()

        now = datetime.now(UTC)

        # 1. Authentic Everyday Retail Customers (Spanning US Metro Regions)
        raw_personas = [
            # San Francisco
            (
                "USR_MARCUS712",
                "Marcus Chen",
                "SF",
                "742 Montgomery St",
                "94111",
                "DEV_MARCUS_IPHONE15",
                "Apple iPhone 15 Pro",
                18500.00,
                28.50,
                65.00,
                14.20,
                ["coffee_shop", "grocery", "restaurant"],
            ),
            (
                "USR_MAYA531",
                "Maya Lin",
                "SF",
                "1200 California St",
                "94109",
                "DEV_MAYA_MACBOOK",
                "Apple MacBook Air M3",
                24200.00,
                34.00,
                75.00,
                16.50,
                ["retail", "grocery", "coffee_shop"],
            ),
            (
                "USR_DAVID518",
                "David Wu",
                "SF",
                "450 Sutter St",
                "94108",
                "DEV_DAVID_PIXEL8",
                "Google Pixel 8 Pro",
                15400.00,
                22.00,
                55.00,
                11.00,
                ["restaurant", "coffee_shop", "fuel"],
            ),
            (
                "USR_NOAH719",
                "Noah Tanaka",
                "SF",
                "88 Colin P Kelly Jr St",
                "94107",
                "DEV_NOAH_GALAXY",
                "Samsung Galaxy S24",
                31000.00,
                42.00,
                95.00,
                21.00,
                ["grocery", "restaurant", "retail"],
            ),
            (
                "USR_ALEXANDER104",
                "Alexander Vance",
                "SF",
                "555 Mission St",
                "94105",
                "DEV_ALEX_IPHONE",
                "Apple iPhone 14 Pro",
                19800.00,
                31.00,
                70.00,
                15.00,
                ["coffee_shop", "restaurant", "fuel"],
            ),
            # New York City
            (
                "USR_ELENA391",
                "Elena Rostova",
                "NYC",
                "150 Central Park South",
                "10019",
                "DEV_ELENA_MACBOOK",
                "Apple MacBook Pro M3 Max",
                58400.00,
                85.00,
                190.00,
                42.00,
                ["restaurant", "retail", "utilities"],
            ),
            (
                "USR_BRIAN812",
                "Brian Vance",
                "NYC",
                "75 Wall Street",
                "10005",
                "DEV_BRIAN_IPHONE15",
                "Apple iPhone 15 Pro Max",
                42000.00,
                65.00,
                150.00,
                32.00,
                ["restaurant", "coffee_shop", "retail"],
            ),
            (
                "USR_CHLOE882",
                "Chloe Martin",
                "NYC",
                "285 Lafayette St",
                "10012",
                "DEV_CHLOE_MACBOOK",
                "Apple MacBook Pro M2",
                27500.00,
                45.00,
                110.00,
                22.00,
                ["coffee_shop", "retail", "restaurant"],
            ),
            (
                "USR_SOPHIA924",
                "Sophia Sterling",
                "NYC",
                "432 Park Ave",
                "10022",
                "DEV_SOPHIA_IPHONE15",
                "Apple iPhone 15",
                36000.00,
                52.00,
                125.00,
                26.00,
                ["grocery", "coffee_shop", "utilities"],
            ),
            (
                "USR_BENJAMIN372",
                "Benjamin Cole",
                "NYC",
                "10 Barclay St",
                "10007",
                "DEV_BEN_THINKPAD",
                "Lenovo ThinkPad X1 Carbon",
                21500.00,
                38.00,
                88.00,
                18.00,
                ["restaurant", "grocery", "fuel"],
            ),
            # Austin Metro
            (
                "USR_SARAH840",
                "Sarah Jenkins",
                "ATX",
                "1100 S Congress Ave",
                "78704",
                "DEV_SARAH_PIXEL8",
                "Google Pixel 8",
                16800.00,
                26.00,
                65.00,
                13.00,
                ["coffee_shop", "grocery", "retail"],
            ),
            (
                "USR_LUCAS275",
                "Lucas Miller",
                "ATX",
                "200 Colorado St",
                "78701",
                "DEV_LUCAS_GALAXY",
                "Samsung Galaxy S23",
                14200.00,
                24.00,
                58.00,
                12.00,
                ["fuel", "grocery", "restaurant"],
            ),
            (
                "USR_ISABELLA420",
                "Isabella Flores",
                "ATX",
                "1603 S 1st St",
                "78704",
                "DEV_ISABELLA_IPHONE",
                "Apple iPhone 13",
                11900.00,
                21.00,
                52.00,
                10.50,
                ["grocery", "coffee_shop", "retail"],
            ),
            (
                "USR_ETHAN305",
                "Ethan Brooks",
                "ATX",
                "301 West Ave",
                "78701",
                "DEV_ETHAN_IPAD",
                "Apple iPad Pro 12.9",
                18900.00,
                29.00,
                72.00,
                14.50,
                ["restaurant", "grocery", "retail"],
            ),
            (
                "USR_GRACE906",
                "Grace Adams",
                "ATX",
                "1221 S MoPac Expy",
                "78746",
                "DEV_GRACE_PIXEL",
                "Google Pixel 7a",
                13500.00,
                23.00,
                55.00,
                11.00,
                ["grocery", "fuel", "coffee_shop"],
            ),
            # Chicago Metro
            (
                "USR_DAVID606",
                "David Miller",
                "CHI",
                "233 S Wacker Dr",
                "60606",
                "DEV_DAVID_GALAXY_CHI",
                "Samsung Galaxy S24 Ultra",
                22400.00,
                35.00,
                80.00,
                17.00,
                ["grocery", "fuel", "retail"],
            ),
            (
                "USR_EMMA611",
                "Emma Kowalski",
                "CHI",
                "875 N Michigan Ave",
                "60611",
                "DEV_EMMA_IPHONE",
                "Apple iPhone 14",
                19500.00,
                32.00,
                75.00,
                16.00,
                ["retail", "restaurant", "coffee_shop"],
            ),
            (
                "USR_MICHAEL601",
                "Michael O'Brien",
                "CHI",
                "111 E Wacker Dr",
                "60601",
                "DEV_MICHAEL_PIXEL",
                "Google Pixel 8",
                26000.00,
                40.00,
                92.00,
                19.00,
                ["restaurant", "grocery", "utilities"],
            ),
            # Seattle Metro
            (
                "USR_SOPHIA981",
                "Sophia Al-Mansoor",
                "SEA",
                "2111 7th Ave",
                "98121",
                "DEV_SOPHIA_SURFACE",
                "Microsoft Surface Laptop 5",
                34500.00,
                48.00,
                110.00,
                23.00,
                ["coffee_shop", "grocery", "utilities"],
            ),
            (
                "USR_KEVIN909",
                "Kevin Patel",
                "SEA",
                "400 9th Ave N",
                "98109",
                "DEV_KEVIN_MACBOOK",
                "Apple MacBook Pro 14",
                39000.00,
                54.00,
                120.00,
                25.00,
                ["restaurant", "retail", "coffee_shop"],
            ),
            (
                "USR_CHLOE901",
                "Chloe Henderson",
                "SEA",
                "1918 8th Ave",
                "98101",
                "DEV_CHLOE_IPHONE",
                "Apple iPhone 15",
                22100.00,
                33.00,
                78.00,
                16.00,
                ["grocery", "restaurant", "retail"],
            ),
            # Boston Metro
            (
                "USR_JAMES610",
                "James O'Connor",
                "BOS",
                "100 Northern Ave",
                "02210",
                "DEV_JAMES_IPAD",
                "Apple iPad Pro M2",
                28900.00,
                41.00,
                95.00,
                20.00,
                ["restaurant", "grocery", "retail"],
            ),
            (
                "USR_CLAIRE021",
                "Claire Walsh",
                "BOS",
                "500 Boylston St",
                "02116",
                "DEV_CLAIRE_IPHONE",
                "Apple iPhone 14 Pro",
                31200.00,
                46.00,
                105.00,
                22.00,
                ["retail", "coffee_shop", "restaurant"],
            ),
            (
                "USR_DANIEL022",
                "Daniel Murphy",
                "BOS",
                "200 State St",
                "02109",
                "DEV_DANIEL_MACBOOK",
                "Apple MacBook Air M2",
                25700.00,
                38.00,
                85.00,
                18.00,
                ["grocery", "fuel", "restaurant"],
            ),
            # Atlanta Metro
            (
                "USR_AMARA433",
                "Amara Okafor",
                "ATL",
                "3344 Peachtree Rd",
                "30326",
                "DEV_AMARA_PIXEL",
                "Google Pixel 8",
                21800.00,
                34.00,
                78.00,
                16.00,
                ["restaurant", "fuel", "retail"],
            ),
            (
                "USR_MARCUS303",
                "Marcus Bell",
                "ATL",
                "1075 Peachtree St NE",
                "30309",
                "DEV_MARCUS_GALAXY",
                "Samsung Galaxy S23+",
                19400.00,
                30.00,
                70.00,
                15.00,
                ["grocery", "fuel", "coffee_shop"],
            ),
            (
                "USR_KENYA363",
                "Kenya Davis",
                "ATL",
                "271 17th St NW",
                "30363",
                "DEV_KENYA_IPHONE",
                "Apple iPhone 13 Pro",
                17500.00,
                27.00,
                62.00,
                13.00,
                ["retail", "grocery", "restaurant"],
            ),
            # Denver Metro
            (
                "USR_LUCAS802",
                "Lucas Silva",
                "DEN",
                "1801 California St",
                "80202",
                "DEV_LUCAS_GALAXY_DEN",
                "Samsung Galaxy S24",
                18200.00,
                28.00,
                68.00,
                14.00,
                ["grocery", "fuel", "coffee_shop"],
            ),
            (
                "USR_HANNAH803",
                "Hannah Scott",
                "DEN",
                "1144 15th St",
                "80202",
                "DEV_HANNAH_IPHONE",
                "Apple iPhone 15 Pro",
                23900.00,
                36.00,
                82.00,
                17.50,
                ["restaurant", "retail", "grocery"],
            ),
            (
                "USR_TYLER804",
                "Tyler Vance",
                "DEN",
                "1700 Lincoln St",
                "80203",
                "DEV_TYLER_PIXEL",
                "Google Pixel 7 Pro",
                16400.00,
                25.00,
                60.00,
                12.00,
                ["fuel", "grocery", "restaurant"],
            ),
            # Los Angeles Metro
            (
                "USR_CHLOE900",
                "Chloe Dubois",
                "LAX",
                "10250 Santa Monica Blvd",
                "90067",
                "DEV_CHLOE_MACBOOK_LAX",
                "Apple MacBook Pro 16 M3",
                52000.00,
                75.00,
                175.00,
                38.00,
                ["restaurant", "retail", "coffee_shop"],
            ),
            (
                "USR_CARLOS967",
                "Carlos Mendez",
                "LAX",
                "1999 Ave of the Stars",
                "90067",
                "DEV_CARLOS_IPHONE",
                "Apple iPhone 15 Pro",
                44500.00,
                62.00,
                145.00,
                31.00,
                ["restaurant", "grocery", "fuel"],
            ),
            (
                "USR_MAYA912",
                "Maya Sterling",
                "LAX",
                "9600 Wilshire Blvd",
                "90212",
                "DEV_MAYA_IPHONE_LAX",
                "Apple iPhone 14 Pro Max",
                61000.00,
                88.00,
                210.00,
                45.00,
                ["retail", "restaurant", "utilities"],
            ),
            # Miami Metro
            (
                "USR_LIAM194",
                "Liam Washington",
                "MIA",
                "1450 Brickell Ave",
                "33131",
                "DEV_LIAM_IPHONE14",
                "Apple iPhone 14 Pro",
                38000.00,
                55.00,
                130.00,
                28.00,
                ["restaurant", "retail", "fuel"],
            ),
            (
                "USR_ISABELLA331",
                "Isabella Rossi",
                "MIA",
                "701 Brickell Ave",
                "33131",
                "DEV_ISABELLA_MACBOOK",
                "Apple MacBook Air 15",
                33500.00,
                49.00,
                115.00,
                24.00,
                ["retail", "restaurant", "coffee_shop"],
            ),
            (
                "USR_MARCO332",
                "Marco Diaz",
                "MIA",
                "200 S Biscayne Blvd",
                "33131",
                "DEV_MARCO_GALAXY",
                "Samsung Galaxy S24+",
                29000.00,
                42.00,
                98.00,
                21.00,
                ["grocery", "fuel", "restaurant"],
            ),
        ]

        # 2. Add Dedicated Victims (for Tor ATO Scenarios)
        for i in range(1, 11):
            victim_id = f"USR_VICTIM{i:02d}"
            city_key = ["SF", "NYC", "ATX", "CHI", "SEA", "BOS", "ATL", "DEN", "LAX", "MIA"][
                (i - 1) % 10
            ]
            raw_personas.append(
                (
                    victim_id,
                    f"Victim Account {i:02d}",
                    city_key,
                    f"{100 * i} Financial Way",
                    "94104",
                    f"DEV_VICTIM_{i:02d}_TRUSTED",
                    "Authorized Apple iPhone",
                    35000.00 + (i * 2500.00),
                    45.00,
                    110.00,
                    22.00,
                    ["grocery", "restaurant", "utilities"],
                )
            )

        # 3. Add Dedicated Smurfing Mules (for BSA Structuring Scenarios)
        for i in range(1, 11):
            smurf_id = f"USR_SMURF{i:02d}"
            city_key = "NYC" if i % 2 == 0 else "MIA"
            raw_personas.append(
                (
                    smurf_id,
                    f"Smurf Mule {i:02d}",
                    city_key,
                    f"{200 * i} Remittance Way",
                    "10001",
                    f"DEV_SMURF_{i:02d}_PROXY",
                    "Disposable Android Device",
                    28000.00,
                    120.00,
                    250.00,
                    60.00,
                    ["money_transfer", "retail"],
                )
            )

        # 4. Backward Compatibility Personas (USR_4401, USR_ALICE401, etc.)
        backward_compat = [
            (
                "USR_4401",
                "Alice Coffeeholder",
                "SF",
                "1 Market St",
                "94105",
                "DEV_COFFEE_01",
                "iPhone 13",
                12000.00,
                6.50,
                12.00,
                2.10,
                ["coffee_shop", "grocery", "restaurant", "fuel"],
            ),
            (
                "USR_4402",
                "Bob Takeover",
                "NYC",
                "100 Wall St",
                "10005",
                "DEV_11AB02",
                "Galaxy S22",
                45000.00,
                74.10,
                109.50,
                19.80,
                ["coffee_shop", "grocery", "fuel", "restaurant"],
            ),
            (
                "USR_4403",
                "Charlie Smurf",
                "MIA",
                "500 Ocean Dr",
                "33139",
                "DEV_SMURF_01",
                "Pixel 7",
                50000.00,
                150.00,
                280.00,
                60.00,
                ["retail", "electronics"],
            ),
            (
                "USR_ALICE401",
                "Alice Standish",
                "SF",
                "100 Pine St",
                "94111",
                "DEV_ALICE_IPHONE",
                "iPhone 14",
                15000.00,
                22.00,
                50.00,
                11.00,
                ["coffee_shop", "grocery", "restaurant"],
            ),
            (
                "USR_BOB402",
                "Robert Langdon",
                "BOS",
                "300 Harvard Yard",
                "02138",
                "DEV_BOB_THINKPAD",
                "ThinkPad X1",
                20000.00,
                28.00,
                65.00,
                14.00,
                ["retail", "coffee_shop"],
            ),
            (
                "USR_CAROL403",
                "Carol Danvers",
                "LAX",
                "500 Grand Ave",
                "90071",
                "DEV_CAROL_MACBOOK",
                "MacBook Pro",
                30000.00,
                45.00,
                110.00,
                22.00,
                ["restaurant", "retail"],
            ),
            (
                "USR_DAN404",
                "Daniel Craig",
                "NYC",
                "40 Wall St",
                "10005",
                "DEV_DAN_IPHONE",
                "iPhone 15 Pro",
                35000.00,
                50.00,
                120.00,
                25.00,
                ["restaurant", "travel"],
            ),
        ]
        raw_personas.extend(backward_compat)

        # Generate relational records for all raw personas
        for item in raw_personas:
            (
                user_id,
                full_name,
                metro_key,
                street,
                zip_code,
                dev_id,
                dev_model,
                init_bal,
                avg_spd,
                p95_spd,
                std_spd,
                cats,
            ) = item
            metro = METRO_REGIONS[metro_key]

            # Customer Profile
            profile = CustomerProfile(
                user_id=user_id,
                full_name=full_name,
                email=f"{user_id.lower()}@aegisbank.com",
                phone=f"+1{random_phone(user_id)}",
                residential_address=f"{street}, {metro['city']}, {metro['state']} {zip_code}",
                city=metro["city"],
                state=metro["state"],
                postal_code=zip_code,
                country="US",
                home_latitude=metro["lat"],
                home_longitude=metro["lon"],
                kyc_status=KycStatus.TIER_3_PASSPORT_VERIFIED,
                credit_score=720 + (hash(user_id) % 120),
                risk_tier=CustomerRiskTier.LOW
                if "SMURF" not in user_id
                else CustomerRiskTier.HIGH_RISK,
                account_opened_at=now - timedelta(days=730),
            )

            # Bank Account (DDA)
            acc_num = f"US89AEGS{abs(hash(user_id)) % 10000000000:010d}"
            account = BankAccount(
                account_number=acc_num,
                user_id=user_id,
                routing_number=metro["routing"],
                account_type=AccountType.CHECKING,
                current_balance=Decimal(str(round(init_bal, 2))),
                available_balance=Decimal(str(round(init_bal, 2))),
                currency="USD",
                status=AccountStatus.ACTIVE,
            )

            # Payment Card
            card_last4 = f"{abs(hash(user_id)) % 10000:04d}"
            card = PaymentCard(
                card_token=f"CARD_{user_id}_{card_last4}",
                user_id=user_id,
                account_number=acc_num,
                masked_pan=f"4111-XXXX-XXXX-{card_last4}",
                card_brand=CardBrand.VISA_SIGNATURE,
                expiry_date="11/28",
                daily_spend_limit=Decimal("5000.00"),
                status=CardStatus.ACTIVE,
            )

            # Device Footprint
            device = DeviceFootprint(
                device_id=dev_id,
                user_id=user_id,
                device_model=dev_model,
                user_agent=(
                    f"Mozilla/5.0 ({dev_model}; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15"
                ),
                trusted_ip_subnet=f"{metro['ip_prefix']}.0/24",
                isp_name=metro["isp"],
                biometric_enrolled=True,
            )

            # Statistical 90-Day Baseline
            baseline = UserBaseline(
                avg_amount=avg_spd,
                std_amount=std_spd,
                median_amount=round(avg_spd * 0.9, 2),
                p95_amount=p95_spd,
                tx_count_90d=120,
                known_categories=cats,
                known_countries=["US"],
                known_devices=[dev_id],
                cold_start=False,
            )

            # Complete Customer Record
            record = BankingCustomerRecord(
                profile=profile,
                accounts=[account],
                cards=[card],
                devices=[device],
                baseline=baseline,
            )

            self._customers[user_id] = record
            self._cards_by_token[card.card_token] = card
            self._cards_by_user[user_id] = [card]

            # Last Known Legitimate Transaction
            self._last_tx_by_user[user_id] = {
                "lat": metro["lat"],
                "lon": metro["lon"],
                "ts": now - timedelta(hours=3),
                "city": metro["city"],
                "country": "US",
                "channel": Channel.CARD_PRESENT,
            }

            # Recent Transactions Ring Buffer
            self._recent_txs_by_user[user_id] = [
                (now - timedelta(days=2), round(avg_spd * 0.8, 2)),
                (now - timedelta(days=1), round(avg_spd * 1.1, 2)),
                (now - timedelta(hours=3), round(avg_spd * 0.95, 2)),
            ]

    # --- Core Banking Operations ---

    def get_customer(self, user_id: str) -> BankingCustomerRecord | None:
        """Fetch full customer record by user_id."""
        with self._data_lock:
            return self._customers.get(user_id)

    def list_all_customers(self) -> list[BankingCustomerRecord]:
        """List all active banking customers."""
        with self._data_lock:
            return list(self._customers.values())

    def get_account(self, user_id: str) -> BankAccount | None:
        """Fetch primary checking account for customer."""
        with self._data_lock:
            record = self._customers.get(user_id)
            return record.accounts[0] if record and record.accounts else None

    def get_card_by_user(self, user_id: str) -> PaymentCard | None:
        """Fetch primary payment card for customer."""
        with self._data_lock:
            cards = self._cards_by_user.get(user_id)
            return cards[0] if cards else None

    def lock_account(self, user_id: str, reason: str = "ATO_DETECTED") -> bool:
        """Enforce account containment: Freeze DDA checking account and payment card."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record:
                return False
            for acc in record.accounts:
                acc.status = AccountStatus.LOCKED_ATO
            for card in record.cards:
                card.status = CardStatus.LOCKED_ATO
            return True

    def challenge_card(self, user_id: str) -> bool:
        """Mark payment card as pending 3DS OTP step-up verification."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record or not record.cards:
                return False
            for card in record.cards:
                card.status = CardStatus.CHALLENGED_3DS
            return True

    def suspend_card(self, user_id: str, reason: str = "EXCEEDED_MAX_3DS_ATTEMPTS") -> bool:
        """Suspend card token following excessive failed or unverified 3DS attempts."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record or not record.cards:
                return False
            for card in record.cards:
                card.status = CardStatus.SUSPENDED
            return True

    def unlock_account(self, user_id: str) -> bool:
        """Analyst override: Restore customer account and cards to ACTIVE."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record:
                return False
            for acc in record.accounts:
                acc.status = AccountStatus.ACTIVE
            for card in record.cards:
                card.status = CardStatus.ACTIVE
            return True

    def reset_all(self) -> int:
        """Reset all customer profiles, balances, cards, and past transaction history to clean state."""
        with self._data_lock:
            self._initialize_records()
            return len(self._customers)

    def is_account_locked(self, user_id: str) -> bool:
        """Return True if customer account or card is currently locked."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record or not record.accounts:
                return False
            return record.accounts[0].status == AccountStatus.LOCKED_ATO

    def debit_account(self, user_id: str, amount: Decimal) -> bool:
        """Settle a legitimate transaction debit against checking account available balance."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record or not record.accounts:
                return False
            acc = record.accounts[0]
            if acc.status != AccountStatus.ACTIVE:
                return False
            if acc.available_balance >= amount:
                acc.available_balance -= amount
                acc.current_balance -= amount
                return True
            return False

    def record_transaction(
        self,
        user_id: str,
        amount: float,
        timestamp: datetime,
        location: dict[str, Any] | None = None,
    ) -> None:
        """Append to recent transaction history and advance last known location."""
        with self._data_lock:
            if user_id not in self._recent_txs_by_user:
                self._recent_txs_by_user[user_id] = []
            self._recent_txs_by_user[user_id].append((timestamp, amount))
            if location:
                self._last_tx_by_user[user_id] = location

    def get_baseline(self, user_id: str) -> UserBaseline:
        """Retrieve 90-day statistical baseline for user or cold-start default."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if record:
                return record.baseline
            return UserBaseline(cold_start=True)

    def is_known_device(self, user_id: str, device_id: str) -> bool:
        """Check if device is recognized in user's enrolled digital devices."""
        with self._data_lock:
            record = self._customers.get(user_id)
            if not record:
                return False
            return any(d.device_id == device_id for d in record.devices)

    def get_last_transaction_location(self, user_id: str) -> dict[str, Any] | None:
        """Fetch coordinates and timestamp of prior transaction."""
        with self._data_lock:
            return self._last_tx_by_user.get(user_id)

    def get_recent_transactions(
        self, user_id: str, limit: int = 50
    ) -> list[tuple[datetime, float]]:
        """Fetch recent chronological transactions."""
        with self._data_lock:
            return self._recent_txs_by_user.get(user_id, [])[-limit:]


def random_phone(seed_str: str) -> str:
    """Generate deterministic phone number from seed."""
    val = abs(hash(seed_str)) % 9000000000 + 1000000000
    return str(val)


# Global singleton instance
bank_db = BankingDatabase()
