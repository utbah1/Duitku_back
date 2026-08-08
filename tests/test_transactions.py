"""Transaction validation, CRUD, and authorization tests."""
import pytest


def test_create_transaction_requires_auth(client, sample_transaction):
    resp = client.post("/api/v1/transactions", json=sample_transaction)
    assert resp.status_code == 401


def test_create_transaction_success(client, auth_headers, sample_transaction):
    resp = client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Makan Siang"
    assert body["amount"] == 25000
    assert body["user_id"] == "test-user-123"
    assert body["id"] is not None


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},
        {"amount": 0},
        {"amount": -5},
        {"type": "invalid"},
        {"category": ""},
    ],
)
def test_create_transaction_validation(client, auth_headers, sample_transaction, overrides):
    payload = {**sample_transaction, **overrides}
    resp = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_transaction_rejects_user_id_from_body(client, auth_headers, sample_transaction):
    """user_id in body should be rejected (schema extra='forbid')."""
    payload = {**sample_transaction, "user_id": "attacker-uid"}
    resp = client.post("/api/v1/transactions", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_get_transaction_not_found(client, auth_headers):
    resp = client.get("/api/v1/transactions/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


def test_get_transaction_success(client, auth_headers, sample_transaction):
    created = client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    ).json()
    tid = created["id"]
    resp = client.get(f"/api/v1/transactions/{tid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == tid


def test_update_transaction(client, auth_headers, sample_transaction):
    created = client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    ).json()
    tid = created["id"]
    resp = client.put(
        f"/api/v1/transactions/{tid}",
        json={"title": "Makan Malam", "amount": 30000},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Makan Malam"
    assert resp.json()["amount"] == 30000


def test_delete_transaction(client, auth_headers, sample_transaction):
    created = client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    ).json()
    tid = created["id"]
    resp = client.delete(f"/api/v1/transactions/{tid}", headers=auth_headers)
    assert resp.status_code == 200
    resp2 = client.get(f"/api/v1/transactions/{tid}", headers=auth_headers)
    assert resp2.status_code == 404


def test_list_transactions_pagination(client, auth_headers, sample_transaction):
    for i in range(5):
        payload = {**sample_transaction, "title": f"Item {i}"}
        client.post("/api/v1/transactions", json=payload, headers=auth_headers)

    resp = client.get("/api/v1/transactions?page=1&limit=2", headers=auth_headers)
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["total_pages"] == 3


def test_list_transactions_filter_by_type(client, auth_headers, sample_transaction):
    client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    )
    income = {**sample_transaction, "type": "income", "title": "Gaji"}
    client.post("/api/v1/transactions", json=income, headers=auth_headers)

    resp = client.get(
        "/api/v1/transactions?type=income", headers=auth_headers
    )
    body = resp.json()
    assert len(body["data"]) == 1
    assert body["data"][0]["type"] == "income"


def test_user_cannot_access_others_transaction(client, auth_headers, sample_transaction):
    created = client.post(
        "/api/v1/transactions", json=sample_transaction, headers=auth_headers
    ).json()
    tid = created["id"]

    from app.core import security

    class OtherVerifier:
        def verify_token(self, token):
            return {"uid": "other-user", "email": "other@example.com"}

    security.token_verifier = OtherVerifier()
    try:
        resp = client.get(f"/api/v1/transactions/{tid}", headers=auth_headers)
        assert resp.status_code == 404
    finally:
        security.token_verifier = security.FirebaseTokenVerifier()
