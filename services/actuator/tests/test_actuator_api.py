"""API tests for the actuator service (mock adapters, no network)."""

from collections.abc import Iterator

import pytest
from aegis_actuator.main import create_app
from aegis_actuator.settings import ActuatorSettings
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = create_app(ActuatorSettings(aegis_adapter_mode="mock", aegis_notifier="log"))
    with TestClient(app) as test_client:
        yield test_client


def _lock(client: TestClient, user_id: str, key: str, case_id: str = "TX_CASE0001") -> object:
    return client.post(
        f"/v1/accounts/{user_id}:lock",
        json={"reason": "H1 Tor + impossible travel", "case_id": case_id},
        headers={"Idempotency-Key": key},
    )


def test_lock_then_get_account(client: TestClient) -> None:
    resp = client.post(
        "/v1/accounts/USR_4402:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers={"Idempotency-Key": "key-0000001"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["locked"] is True
    assert body["replayed"] is False
    assert body["already_locked"] is False

    status = client.get("/v1/accounts/USR_4402")
    assert status.status_code == 200
    assert status.json()["locked"] is True
    assert status.json()["case_id"] == "TX_ATO0001"


def test_lock_requires_idempotency_key(client: TestClient) -> None:
    resp = client.post("/v1/accounts/USR_4402:lock", json={"reason": "H1", "case_id": "TX_ATO0001"})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_lock_replay_with_same_key_does_not_reexecute(client: TestClient) -> None:
    headers = {"Idempotency-Key": "key-replay-01"}
    body = {"reason": "H1", "case_id": "TX_ATO0001"}
    first = client.post("/v1/accounts/USR_4402:lock", json=body, headers=headers)
    second = client.post("/v1/accounts/USR_4402:lock", json=body, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["replayed"] is True
    assert second.json()["updated_at"] == first.json()["updated_at"]


def test_idempotency_key_reuse_for_different_request_conflicts(client: TestClient) -> None:
    headers = {"Idempotency-Key": "key-conflict-1"}
    ok = client.post(
        "/v1/accounts/USR_4402:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers=headers,
    )
    conflict = client.post(
        "/v1/accounts/USR_9999:lock",
        json={"reason": "H1", "case_id": "TX_ATO0002"},
        headers=headers,
    )
    assert ok.status_code == 200
    assert conflict.status_code == 409
    assert conflict.json()["type"] == "urn:aegis:error:idempotency-conflict"


def test_second_lock_with_new_key_is_noop(client: TestClient) -> None:
    client.post(
        "/v1/accounts/USR_4402:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers={"Idempotency-Key": "key-first-001"},
    )
    again = client.post(
        "/v1/accounts/USR_4402:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers={"Idempotency-Key": "key-second-01"},
    )
    assert again.status_code == 200
    assert again.json()["already_locked"] is True


def test_unlock_requires_reason(client: TestClient) -> None:
    client.post(
        "/v1/accounts/USR_4402:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers={"Idempotency-Key": "key-unlock-01"},
    )
    missing = client.post("/v1/accounts/USR_4402:unlock", json={})
    assert missing.status_code == 422
    ok = client.post("/v1/accounts/USR_4402:unlock", json={"reason": "Customer verified by phone"})
    assert ok.status_code == 200
    assert ok.json()["locked"] is False


def test_unlock_unknown_account_is_404(client: TestClient) -> None:
    resp = client.post("/v1/accounts/USR_0000:unlock", json={"reason": "verified"})
    assert resp.status_code == 404
    assert resp.json()["status"] == 404


def test_invalid_user_id_is_rejected(client: TestClient) -> None:
    resp = client.post(
        "/v1/accounts/not-a-user:lock",
        json={"reason": "H1", "case_id": "TX_ATO0001"},
        headers={"Idempotency-Key": "key-invalid-1"},
    )
    assert resp.status_code == 422


def test_block_transaction_is_idempotent(client: TestClient) -> None:
    first = client.post("/v1/transactions/TX_SMURF001:block", json={"reason": "H2"})
    second = client.post("/v1/transactions/TX_SMURF001:block", json={"reason": "H2"})
    assert first.json()["newly_blocked"] is True
    assert second.json()["newly_blocked"] is False
    assert second.json()["blocked"] is True


def test_dispatch_alert(client: TestClient) -> None:
    resp = client.post(
        "/v1/alerts",
        json={"user_id": "USR_4402", "channel": "SMS", "message": "Your account was locked"},
    )
    assert resp.status_code == 200
    assert resp.json()["delivered"] is True


def test_alert_rejects_unknown_channel(client: TestClient) -> None:
    resp = client.post(
        "/v1/alerts", json={"user_id": "USR_4402", "channel": "PIGEON", "message": "hi"}
    )
    assert resp.status_code == 422


def test_requests_refused_outside_mock_mode() -> None:
    app = create_app(ActuatorSettings(aegis_adapter_mode="unsupported"))
    # Startup must fail closed: unsupported adapters fail closed.
    with pytest.raises(RuntimeError, match="not implemented"), TestClient(app):
        pass
