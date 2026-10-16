"""In-memory mock ProfileStore seeded with representative BFSI test personas."""

from datetime import UTC, datetime, timedelta
from typing import Any

from aegis_common.banking import bank_db
from aegis_common.schemas.enums import Channel
from aegis_common.schemas.features import UserBaseline


class InMemoryProfileStore:
    """Deterministic in-memory implementation of ProfileStore for tests and offline mock mode."""

    def __init__(self) -> None:
        now = datetime.now(UTC)
        self.profiles: dict[str, dict[str, Any]] = {
            # Persona 1: Clean Coffee drinker (95% fast path)
            "USR_4401": {
                "baseline": UserBaseline(
                    avg_amount=6.50,
                    std_amount=2.10,
                    median_amount=5.80,
                    p95_amount=12.00,
                    tx_count_90d=142,
                    known_categories=["coffee_shop", "grocery", "restaurant", "fuel"],
                    known_countries=["US"],
                    known_devices=["DEV_COFFEE_01"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_COFFEE_01"},
                "last_tx": {
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "ts": now - timedelta(hours=2),
                    "city": "San Francisco",
                    "country": "US",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [
                    (now - timedelta(hours=24), 5.25),
                    (now - timedelta(hours=2), 4.75),
                ],
            },
            # Persona 2: Impossible Travel Account Takeover victim
            "USR_4402": {
                "baseline": UserBaseline(
                    avg_amount=74.10,
                    std_amount=19.80,
                    median_amount=71.00,
                    p95_amount=109.50,
                    tx_count_90d=61,
                    known_categories=["coffee_shop", "grocery", "fuel", "restaurant"],
                    known_countries=["AE", "OM"],
                    known_devices=["DEV_11AB02", "DEV_77CD10"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_11AB02", "DEV_77CD10"},
                "last_tx": {
                    "lat": 25.2048,
                    "lon": 55.2708,
                    "ts": now - timedelta(minutes=12),  # 12 min ago in Dubai
                    "city": "Dubai",
                    "country": "AE",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [
                    (now - timedelta(days=1), 42.0),
                    (now - timedelta(minutes=12), 35.50),
                ],
            },
            # Persona 3: Near-threshold structuring smurfer
            "USR_4403": {
                "baseline": UserBaseline(
                    avg_amount=150.0,
                    std_amount=60.0,
                    median_amount=135.0,
                    p95_amount=280.0,
                    tx_count_90d=40,
                    known_categories=["retail", "electronics"],
                    known_countries=["US"],
                    known_devices=["DEV_SMURF_01"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_SMURF_01"},
                "last_tx": {
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "ts": now - timedelta(minutes=4),
                    "city": "New York",
                    "country": "US",
                    "channel": Channel.ECOMMERCE,
                },
                "recent_txs": [
                    (now - timedelta(minutes=11), 9450.0),
                    (now - timedelta(minutes=4), 9800.0),
                ],
            },
            # Live simulation personas
            "USR_ALICE401": {
                "baseline": UserBaseline(
                    avg_amount=22.0,
                    std_amount=8.0,
                    median_amount=20.0,
                    p95_amount=45.0,
                    tx_count_90d=140,
                    known_categories=["coffee_shop", "grocery", "restaurant"],
                    known_countries=["US"],
                    known_devices=["DEV_ALICE_IPHONE15"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_ALICE_IPHONE15"},
                "last_tx": {
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "ts": now - timedelta(hours=3),
                    "city": "San Francisco",
                    "country": "US",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [(now - timedelta(hours=24), 18.5), (now - timedelta(hours=3), 22.0)],
            },
            "USR_BRIAN812": {
                "baseline": UserBaseline(
                    avg_amount=65.0,
                    std_amount=22.0,
                    median_amount=60.0,
                    p95_amount=120.0,
                    tx_count_90d=110,
                    known_categories=["restaurant", "retail", "utilities"],
                    known_countries=["US"],
                    known_devices=["DEV_BRIAN_MACBOOK"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_BRIAN_MACBOOK"},
                "last_tx": {
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "ts": now - timedelta(hours=4),
                    "city": "New York",
                    "country": "US",
                    "channel": Channel.ECOMMERCE,
                },
                "recent_txs": [(now - timedelta(hours=24), 55.0), (now - timedelta(hours=4), 70.0)],
            },
            "USR_CHLOE319": {
                "baseline": UserBaseline(
                    avg_amount=32.0,
                    std_amount=12.0,
                    median_amount=30.0,
                    p95_amount=65.0,
                    tx_count_90d=130,
                    known_categories=["coffee_shop", "fuel", "grocery"],
                    known_countries=["US"],
                    known_devices=["DEV_CHLOE_PIXEL8"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_CHLOE_PIXEL8"},
                "last_tx": {
                    "lat": 30.2672,
                    "lon": -97.7431,
                    "ts": now - timedelta(hours=5),
                    "city": "Austin",
                    "country": "US",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [(now - timedelta(hours=24), 28.0), (now - timedelta(hours=5), 35.0)],
            },
            "USR_DAVID604": {
                "baseline": UserBaseline(
                    avg_amount=45.0,
                    std_amount=15.0,
                    median_amount=42.0,
                    p95_amount=85.0,
                    tx_count_90d=95,
                    known_categories=["grocery", "retail", "utilities"],
                    known_countries=["US"],
                    known_devices=["DEV_DAVID_GALAXY24"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_DAVID_GALAXY24"},
                "last_tx": {
                    "lat": 47.6062,
                    "lon": -122.3321,
                    "ts": now - timedelta(hours=6),
                    "city": "Seattle",
                    "country": "US",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [(now - timedelta(hours=24), 40.0), (now - timedelta(hours=6), 48.0)],
            },
            "USR_CAROL915": {
                "baseline": UserBaseline(
                    avg_amount=74.10,
                    std_amount=19.80,
                    median_amount=71.00,
                    p95_amount=109.50,
                    tx_count_90d=61,
                    known_categories=["coffee_shop", "grocery", "fuel", "restaurant"],
                    known_countries=["AE", "OM"],
                    known_devices=["DEV_CAROL_SAFE"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_CAROL_SAFE"},
                "last_tx": {
                    "lat": 25.2048,
                    "lon": 55.2708,
                    "ts": now - timedelta(minutes=12),
                    "city": "Dubai",
                    "country": "AE",
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": [
                    (now - timedelta(days=1), 42.0),
                    (now - timedelta(minutes=12), 35.5),
                ],
            },
            "USR_SMURF99": {
                "baseline": UserBaseline(
                    avg_amount=150.0,
                    std_amount=60.0,
                    median_amount=135.0,
                    p95_amount=280.0,
                    tx_count_90d=40,
                    known_categories=["retail", "electronics"],
                    known_countries=["US"],
                    known_devices=["DEV_LEGIT"],
                    cold_start=False,
                ),
                "known_devices": {"DEV_LEGIT"},
                "last_tx": {
                    "lat": 40.7128,
                    "lon": -74.0060,
                    "ts": now - timedelta(minutes=4),
                    "city": "New York",
                    "country": "US",
                    "channel": Channel.ECOMMERCE,
                },
                "recent_txs": [
                    (now - timedelta(minutes=11), 9450.0),
                    (now - timedelta(minutes=4), 9800.0),
                ],
            },
        }

        # Seed rich personas for large-scale real-world testing
        extra_personas = [
            (
                "USR_MARCUS712",
                "DEV_MARCUS_IPHONE15",
                37.7749,
                -122.4194,
                "San Francisco",
                "US",
                25.0,
                10.0,
                65.0,
            ),
            (
                "USR_SARAH840",
                "DEV_SARAH_PIXEL8",
                30.2672,
                -97.7431,
                "Austin",
                "US",
                35.0,
                15.0,
                85.0,
            ),
            (
                "USR_ELENA391",
                "DEV_ELENA_MACBOOK",
                40.7128,
                -74.0060,
                "New York",
                "US",
                65.0,
                25.0,
                180.0,
            ),
            (
                "USR_DAVID518",
                "DEV_DAVID_GALAXY",
                41.8781,
                -87.6298,
                "Chicago",
                "US",
                30.0,
                12.0,
                75.0,
            ),
            (
                "USR_SOPHIA924",
                "DEV_SOPHIA_IPHONE15",
                47.6062,
                -122.3321,
                "Seattle",
                "US",
                28.0,
                11.0,
                80.0,
            ),
            (
                "USR_JAMES610",
                "DEV_JAMES_IPAD",
                42.3601,
                -71.0589,
                "Boston",
                "US",
                48.0,
                18.0,
                120.0,
            ),
            (
                "USR_AMARA433",
                "DEV_AMARA_PIXEL",
                33.7490,
                -84.3880,
                "Atlanta",
                "US",
                38.0,
                14.0,
                95.0,
            ),
            (
                "USR_LUCAS275",
                "DEV_LUCAS_GALAXY",
                39.7392,
                -104.9903,
                "Denver",
                "US",
                29.0,
                10.0,
                75.0,
            ),
            (
                "USR_CHLOE882",
                "DEV_CHLOE_MACBOOK",
                34.0522,
                -118.2437,
                "Los Angeles",
                "US",
                55.0,
                22.0,
                160.0,
            ),
            (
                "USR_LIAM194",
                "DEV_LIAM_IPHONE14",
                25.7617,
                -80.1918,
                "Miami",
                "US",
                45.0,
                18.0,
                130.0,
            ),
            (
                "USR_ETHAN305",
                "DEV_ETHAN_SURFACE",
                32.7767,
                -96.7970,
                "Dallas",
                "US",
                40.0,
                16.0,
                95.0,
            ),
            (
                "USR_ISABELLA420",
                "DEV_ISABELLA_IPHONE",
                33.4484,
                -112.0740,
                "Phoenix",
                "US",
                50.0,
                20.0,
                140.0,
            ),
            (
                "USR_NOAH719",
                "DEV_NOAH_PIXEL7",
                32.7157,
                -117.1611,
                "San Diego",
                "US",
                32.0,
                12.0,
                70.0,
            ),
            (
                "USR_MAYA531",
                "DEV_MAYA_MACBOOK",
                38.9072,
                -77.0369,
                "Washington",
                "US",
                60.0,
                24.0,
                150.0,
            ),
            (
                "USR_OLIVER614",
                "DEV_OLIVER_GALAXY",
                39.9526,
                -75.1652,
                "Philadelphia",
                "US",
                46.0,
                17.0,
                115.0,
            ),
            (
                "USR_CHARLOTTE228",
                "DEV_CHARLOTTE_IPHONE",
                43.6532,
                -79.3832,
                "Toronto",
                "CA",
                40.0,
                15.0,
                85.0,
            ),
            (
                "USR_ALEXANDER104",
                "DEV_ALEX_THINKPAD",
                51.5074,
                -0.1278,
                "London",
                "GB",
                68.0,
                26.0,
                175.0,
            ),
            (
                "USR_MIA819",
                "DEV_MIA_MACBOOKAIR",
                52.3676,
                4.9041,
                "Amsterdam",
                "NL",
                42.0,
                16.0,
                95.0,
            ),
            (
                "USR_BENJAMIN372",
                "DEV_BEN_IPHONE15",
                50.1109,
                8.6821,
                "Frankfurt",
                "DE",
                52.0,
                19.0,
                110.0,
            ),
            (
                "USR_GRACE906",
                "DEV_GRACE_XPERIA",
                35.6762,
                139.6503,
                "Tokyo",
                "JP",
                36.0,
                14.0,
                80.0,
            ),
        ]
        for uid, dev, lat, lon, city, country, avg_amt, std_amt, p95 in extra_personas:
            self.profiles[uid] = {
                "baseline": UserBaseline(
                    avg_amount=avg_amt,
                    std_amount=std_amt,
                    median_amount=round(avg_amt * 0.9, 2),
                    p95_amount=p95,
                    tx_count_90d=120,
                    known_categories=[
                        "coffee_shop",
                        "grocery",
                        "restaurant",
                        "retail",
                        "fuel",
                        "utilities",
                    ],
                    known_countries=[country, "US"] if country != "US" else ["US"],
                    known_devices=[dev],
                    cold_start=False,
                ),
                "known_devices": {dev},
                "last_tx": {
                    "lat": lat,
                    "lon": lon,
                    "ts": (
                        now - timedelta(minutes=14)
                        if uid == "USR_ELENA391"
                        else now - timedelta(hours=3)
                    ),
                    "city": city,
                    "country": country,
                    "channel": Channel.CARD_PRESENT,
                },
                "recent_txs": (
                    [
                        (now - timedelta(minutes=11), 9450.0),
                        (now - timedelta(minutes=4), 9750.0),
                    ]
                    if uid == "USR_SARAH840"
                    else [
                        (now - timedelta(hours=24), round(avg_amt * 0.8, 2)),
                        (now - timedelta(hours=3), round(avg_amt * 1.05, 2)),
                    ]
                ),
            }

    async def get_baseline(self, user_id: str) -> UserBaseline:
        """Fetch user baseline from banking database, memory profiles, or default."""
        profile = self.profiles.get(user_id)
        if profile and "baseline" in profile:
            return profile["baseline"]  # type: ignore[no-any-return]
        customer = bank_db.get_customer(user_id)
        if customer:
            return customer.baseline
        if user_id.startswith(("USR_BN", "USR_LIVE", "USR_SIM", "USR_VICTIM")):
            return UserBaseline(
                avg_amount=55.0,
                std_amount=18.0,
                median_amount=50.0,
                p95_amount=120.0,
                known_categories=[
                    "coffee_shop",
                    "grocery",
                    "restaurant",
                    "retail",
                    "fuel",
                    "utilities",
                ],
                known_countries=["US", "GB", "DE"],
                known_devices=[f"DEV_{user_id}_DEVICE"],
                cold_start=False,
            )
        if user_id.startswith("USR_SMURF"):
            return UserBaseline(
                avg_amount=150.0,
                std_amount=60.0,
                median_amount=135.0,
                p95_amount=280.0,
                tx_count_90d=40,
                known_categories=["retail", "electronics"],
                known_countries=["US"],
                known_devices=["DEV_LEGIT"],
                cold_start=False,
            )
        return UserBaseline(cold_start=True)

    async def get_recent_transactions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[tuple[datetime, float]]:
        """Fetch user recent transactions ordered chronologically."""
        profile = self.profiles.get(user_id)
        if profile and "recent_txs" in profile and profile["recent_txs"]:
            txs = profile["recent_txs"]
            return list(txs[-limit:])
        return bank_db.get_recent_transactions(user_id, limit=limit)

    async def get_last_transaction_location(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Fetch location and timestamp of previous transaction."""
        profile = self.profiles.get(user_id)
        if profile and "last_tx" in profile and profile["last_tx"] is not None:
            return profile["last_tx"]  # type: ignore[no-any-return]
        last_tx = bank_db.get_last_transaction_location(user_id)
        if last_tx:
            return last_tx
        if user_id.startswith("USR_VICTIM"):
            now = datetime.now(UTC)
            return {
                "lat": 25.2048,
                "lon": 55.2708,
                "ts": now - timedelta(minutes=15),
                "city": "Dubai",
                "country": "AE",
                "channel": Channel.CARD_PRESENT,
            }
        return None

    async def is_known_device(self, user_id: str, device_id: str) -> bool:
        """Check if device is recognized in customer's registered hardware."""
        profile = self.profiles.get(user_id)
        if profile and "known_devices" in profile:
            return device_id in profile["known_devices"]
        if bank_db.get_customer(user_id):
            return bank_db.is_known_device(user_id, device_id)
        return (
            device_id.startswith("DEV_KNOWN")
            or f"DEV_{user_id}" in device_id
            or "LEGIT" in device_id
        )

    async def record_transaction(
        self,
        user_id: str,
        amount: float,
        timestamp: datetime,
        location: dict[str, Any] | None = None,
        device_id: str | None = None,
    ) -> None:
        """Record an incoming transaction to maintain rolling sliding windows."""
        bank_db.record_transaction(user_id, amount, timestamp, location)
        if user_id not in self.profiles:
            baseline = await self.get_baseline(user_id)
            self.profiles[user_id] = {
                "baseline": baseline,
                "known_devices": {device_id} if device_id else set(),
                "recent_txs": [],
                "last_tx": None,
            }
        profile = self.profiles[user_id]
        profile.setdefault("recent_txs", []).append((timestamp, amount))
        profile["recent_txs"] = sorted(profile["recent_txs"], key=lambda x: x[0])[-100:]
        if location:
            profile["last_tx"] = {
                "lat": location.get("lat", 0.0),
                "lon": location.get("lon", 0.0),
                "ts": timestamp,
                "city": location.get("city", "Unknown"),
                "country": location.get("country", "US"),
                "channel": location.get("channel", Channel.CARD_PRESENT),
            }
