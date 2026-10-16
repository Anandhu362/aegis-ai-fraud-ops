"""Unit and API tests for agent-engine HTTP endpoints."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from aegis_common.schemas.enums import Channel, Decision, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction
from aegis_engine.main import create_app
from aegis_engine.settings import EngineSettings
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(EngineSettings(aegis_adapter_mode="mock"))
    with TestClient(app) as test_client:
        yield test_client


def test_engine_health_endpoints(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    resp_ready = client.get("/readyz")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "ready"


def test_internal_investigate_clean_coffee(client: TestClient) -> None:
    tx = Transaction(
        tx_id="TX_COFFEE001",
        user_id="USR_4401",
        amount=Decimal("4.50"),
        currency="USD",
        timestamp=datetime.now(UTC),
        merchant="Blue Bottle Coffee",
        merchant_category=MerchantCategory.COFFEE_SHOP,
        channel=Channel.CARD_PRESENT,
        location=Location(
            latitude=37.7749, longitude=-122.4194, city="San Francisco", country="US"
        ),
        device_id="DEV_COFFEE_01",
    )

    resp = client.post("/internal/investigate", json=tx.model_dump(mode="json"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["tx_id"] == "TX_COFFEE001"
    assert body["decision"] == Decision.ALLOW
    assert body["threat_score"] == 0
