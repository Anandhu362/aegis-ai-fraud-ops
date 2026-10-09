"""Unit tests for aegis-common schemas."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from aegis_common.schemas.enums import Channel, Decision, MerchantCategory, RiskLevel
from aegis_common.schemas.transaction import Location, Transaction
from aegis_common.schemas.verdict import Verdict
from pydantic import ValidationError as PydanticValidationError


def test_valid_transaction() -> None:
    """Test valid transaction creation and field enforcement."""
    tx = Transaction(
        tx_id="TX_1001",
        user_id="USR_42",
        timestamp=datetime.now(UTC),
        amount=Decimal("125.50"),
        currency="USD",
        merchant="Artisan Coffee Roasters",
        merchant_category=MerchantCategory.COFFEE_SHOP,
        channel=Channel.CARD_PRESENT,
        device_id="DEV_9912",
        location=Location(
            latitude=25.2048,
            longitude=55.2708,
            city="Dubai",
            country="AE",
        ),
    )
    assert tx.tx_id == "TX_1001"
    assert tx.amount == Decimal("125.50")
    assert tx.merchant_category == MerchantCategory.COFFEE_SHOP


def test_invalid_transaction_amount() -> None:
    """Amount <= 0 should fail validation."""
    with pytest.raises(PydanticValidationError):
        Transaction(
            tx_id="TX_1001",
            user_id="USR_42",
            timestamp=datetime.now(UTC),
            amount=Decimal("0.00"),
            currency="USD",
            merchant="Coffee",
            merchant_category=MerchantCategory.COFFEE_SHOP,
            device_id="DEV_1",
            location=Location(
                latitude=0.0,
                longitude=0.0,
                city="Test",
                country="US",
            ),
        )


def test_verdict_bounded_score() -> None:
    """Threat score must be between 0 and 100."""
    verdict = Verdict(
        tx_id="TX_1001",
        user_id="USR_42",
        threat_score=85,
        risk_level=RiskLevel.HIGH,
        decision=Decision.BLOCK_TX,
        rationale="High travel velocity detected.",
    )
    assert verdict.threat_score == 85
    assert verdict.risk_level == RiskLevel.HIGH
