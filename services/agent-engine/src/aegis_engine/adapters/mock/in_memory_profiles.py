"""In-memory mock ProfileStore seeded with representative BFSI test personas."""

from datetime import UTC, datetime, timedelta
from typing import Any

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
        }

    async def get_baseline(self, user_id: str) -> UserBaseline:
        """Fetch user baseline or return a cold-start default."""
        profile = self.profiles.get(user_id)
        if profile and "baseline" in profile:
            return profile["baseline"]  # type: ignore[no-any-return]
        return UserBaseline(cold_start=True)

    async def get_recent_transactions(
        self,
        user_id: str,
        limit: int = 50,
    ) -> list[tuple[datetime, float]]:
        """Fetch user recent transactions ordered chronologically."""
        profile = self.profiles.get(user_id)
        if profile and "recent_txs" in profile:
            txs = profile["recent_txs"]
            return list(txs[-limit:])
        return []

    async def get_last_transaction_location(
        self,
        user_id: str,
    ) -> dict[str, Any] | None:
        """Fetch location and timestamp of previous transaction."""
        profile = self.profiles.get(user_id)
        if profile and "last_tx" in profile:
            return profile["last_tx"]  # type: ignore[no-any-return]
        return None

    async def is_known_device(self, user_id: str, device_id: str) -> bool:
        """Check if device is recognized."""
        profile = self.profiles.get(user_id)
        if profile and "known_devices" in profile:
            return device_id in profile["known_devices"]
        return False
