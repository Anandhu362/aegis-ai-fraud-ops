"""Predefined transaction scenarios for live demo buttons and testing."""

from datetime import UTC, datetime
from decimal import Decimal

from aegis_common.schemas.enums import Channel, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction


def create_clean_coffee_scenario(tx_id: str = "TX_COFFEE001") -> Transaction:
    """Scenario 1: Benign everyday coffee transaction ($4.50, home city, clean IP).

    Fast-path triage: Score = 0 -> ALLOW in < 1s (zero LLM inference).
    """
    return Transaction(
        tx_id=tx_id,
        user_id="USR_4401",
        timestamp=datetime.now(UTC),
        amount=Decimal("4.50"),
        currency="USD",
        merchant="Blue Bottle Coffee",
        merchant_category=MerchantCategory.COFFEE_SHOP,
        channel=Channel.CARD_PRESENT,
        device_id="DEV_COFFEE_01",
        ip_address="73.189.42.11",  # type: ignore[arg-type]
        location=Location(
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco",
            country="US",
        ),
    )


def create_smurfing_scenario(tx_id: str = "TX_SMURF001") -> Transaction:
    """Scenario 2: Near-threshold structuring smurfing ($9,800 money transfer).

    Prior transactions in $8k-$10k window trigger structuring_hit and H2 hard floor.
    """
    return Transaction(
        tx_id=tx_id,
        user_id="USR_4403",
        timestamp=datetime.now(UTC),
        amount=Decimal("9800.00"),
        currency="USD",
        merchant="Fast Wire Transfers LLC",
        merchant_category=MerchantCategory.MONEY_TRANSFER,
        channel=Channel.ECOMMERCE,
        device_id="DEV_SMURF_01",
        ip_address="73.189.42.11",  # type: ignore[arg-type]
        location=Location(
            latitude=40.7128,
            longitude=-74.0060,
            city="New York",
            country="US",
        ),
    )


def create_tor_travel_scenario(tx_id: str = "TX_ATO001") -> Transaction:
    """Scenario 3: Impossible travel + Tor exit node Account Takeover ($12,500 crypto).

    Victim in Dubai 12 min ago -> London e-com transaction over Tor exit node.
    Triggers S1, S2, S3, S6, S8, S9, S10 and H1 hard floor -> LOCK_ACCOUNT (early containment).
    """
    return Transaction(
        tx_id=tx_id,
        user_id="USR_4402",
        timestamp=datetime.now(UTC),
        amount=Decimal("12500.00"),
        currency="USD",
        merchant="Global Crypto Exchange Inc",
        merchant_category=MerchantCategory.CRYPTOCURRENCY_BROKERAGE,
        channel=Channel.ECOMMERCE,
        device_id="DEV_UNKNOWN_HACKER",
        ip_address="185.220.101.5",  # type: ignore[arg-type]
        location=Location(
            latitude=51.5074,
            longitude=-0.1278,
            city="London",
            country="GB",
        ),
    )
