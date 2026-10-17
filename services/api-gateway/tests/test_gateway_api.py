"""API and contract tests for api-gateway service."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from aegis_common.schemas.enums import Channel, Decision, MerchantCategory
from aegis_common.schemas.transaction import Location, Transaction
from aegis_gateway.main import create_app
from aegis_gateway.settings import GatewaySettings
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(GatewaySettings(aegis_adapter_mode="mock"))
    with TestClient(app) as test_client:
        yield test_client


def _sample_tx(tx_id: str = "TX_COFFEE001") -> Transaction:
    return Transaction(
        tx_id=tx_id,
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


def test_healthz_and_readyz(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_analyze_transaction_sync(client: TestClient) -> None:
    tx = _sample_tx("TX_SYNC001")
    resp = client.post("/v1/transactions:analyze?mode=sync", json=tx.model_dump(mode="json"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["tx_id"] == "TX_SYNC001"
    assert body["decision"] == Decision.ALLOW
    assert body["threat_score"] == 0


def test_v0_alias_analyze_tx(client: TestClient) -> None:
    tx = _sample_tx("TX_ALIAS001")
    resp = client.post("/api/analyze-tx", json=tx.model_dump(mode="json"))
    assert resp.status_code == 200
    assert resp.json()["tx_id"] == "TX_ALIAS001"


def test_duplicate_tx_id_returns_409_conflict(client: TestClient) -> None:
    tx = _sample_tx("TX_DUP001")
    resp1 = client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))
    assert resp1.status_code == 200

    resp2 = client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))
    assert resp2.status_code == 409
    body = resp2.json()
    assert body["type"] == "urn:aegis:error:duplicate-transaction"
    assert resp2.headers["content-type"].startswith("application/problem+json")


def test_invalid_payload_returns_422_problem_details(client: TestClient) -> None:
    resp = client.post("/v1/transactions:analyze", json={"invalid": "payload"})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["type"] == "urn:aegis:error:validation"


def test_get_investigation_and_404_handling(client: TestClient) -> None:
    tx = _sample_tx("TX_LOOKUP001")
    client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))

    lookup = client.get("/v1/investigations/TX_LOOKUP001")
    assert lookup.status_code == 200
    assert lookup.json()["tx_id"] == "TX_LOOKUP001"

    missing = client.get("/v1/investigations/TX_NONEXISTENT")
    assert missing.status_code == 404
    assert missing.json()["type"] == "urn:aegis:error:not-found"


def test_analyst_decision_override(client: TestClient) -> None:
    tx = _sample_tx("TX_DECISION001")
    client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))

    override_payload = {
        "action": "APPROVE",
        "reason": "Customer confirmed legitimate transaction over phone",
        "analyst_uid": "analyst_sarah_01",
        "at": 1728864000000,
    }
    decision_resp = client.post(
        "/v1/investigations/TX_DECISION001/decision",
        json=override_payload,
    )
    assert decision_resp.status_code == 200
    body = decision_resp.json()
    assert body["analyst_decision"]["action"] == "APPROVE"


def test_simulation_scenarios_coffee_smurfing_tor(client: TestClient) -> None:
    # 1. Clean coffee
    resp_coffee = client.post("/v1/simulations/coffee")
    assert resp_coffee.status_code == 200
    assert resp_coffee.json()["decision"] == Decision.ALLOW

    # 2. Smurfing
    resp_smurf = client.post("/v1/simulations/smurfing")
    assert resp_smurf.status_code == 200
    assert resp_smurf.json()["decision"] in (Decision.BLOCK_TX, Decision.LOCK_ACCOUNT)

    # 3. Tor ATO
    resp_tor = client.post("/v1/simulations/tor_travel")
    assert resp_tor.status_code == 200
    assert resp_tor.json()["decision"] == Decision.LOCK_ACCOUNT

    # 4. 3DS Step-Up Challenge
    resp_3ds = client.post("/v1/simulations/challenge_3ds")
    assert resp_3ds.status_code == 200
    assert resp_3ds.json()["decision"] == Decision.CHALLENGE_3DS
    assert resp_3ds.json()["actuator_action"]["challenge_initiated"] is True


def test_simulation_unknown_scenario_returns_validation_error(client: TestClient) -> None:
    resp = client.post("/v1/simulations/unknown_attack")
    assert resp.status_code == 400
    assert resp.json()["type"] == "urn:aegis:error:validation"


def test_metrics_summary(client: TestClient) -> None:
    client.post("/v1/simulations/coffee")
    client.post("/v1/simulations/tor_travel")

    metrics = client.get("/v1/metrics/summary")
    assert metrics.status_code == 200
    data = metrics.json()
    assert data["last_eval_status"] == "BENCHMARK_GREEN"
    assert "processed_count" in data


def test_list_investigations(client: TestClient) -> None:
    tx = _sample_tx("TX_LIST001")
    client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))
    resp = client.get("/v1/investigations?limit=10")
    assert resp.status_code == 200
    cases = resp.json()
    assert isinstance(cases, list)
    assert len(cases) > 0
    assert any(c["tx_id"] == "TX_LIST001" for c in cases)


def test_clear_investigations(client: TestClient) -> None:
    tx = _sample_tx("TX_CLEAR001")
    client.post("/v1/transactions:analyze", json=tx.model_dump(mode="json"))
    resp_before = client.get("/v1/investigations?limit=10")
    assert len(resp_before.json()) > 0

    clear_resp = client.post("/v1/investigations:clear")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "cleared"

    resp_after = client.get("/v1/investigations?limit=10")
    assert resp_after.status_code == 200
    assert len(resp_after.json()) == 0

    metrics = client.get("/v1/metrics/summary").json()
    assert metrics["processed_count"] == 0


def test_auth_login_and_logout(client: TestClient) -> None:
    bad_resp = client.post("/v1/auth/login", json={"email": "demo@aegis.com", "password": "wrong"})
    assert bad_resp.status_code == 401

    resp = client.post("/v1/auth/login", json={"email": "demo@aegis.com", "password": "password"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    token = data["access_token"]
    assert data["analyst"]["email"] == "demo@aegis.com"
    assert data["analyst"]["role"] == "L2 Senior Fraud Ops"

    # Verify session via /v1/auth/me
    me_resp = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Anandhu"
    assert me_data["email"] == "demo@aegis.com"

    # Missing auth fails
    me_unauth = client.get("/v1/auth/me")
    assert me_unauth.status_code == 401

    # Logout revokes token
    logout_resp = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Token after logout is rejected
    me_revoked = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_revoked.status_code == 401


def test_policies_endpoint(client: TestClient) -> None:
    resp = client.get("/v1/policies")
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_version"] == "v1.1"
    assert len(data["hard_floors"]) >= 3
    assert data["containment_rule"]["min_score"] == 85
