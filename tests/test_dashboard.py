"""Dashboard tests."""


def _seed(client, headers):
    client.post(
        "/api/v1/transactions",
        json={"title": "Gaji", "amount": 100000, "category": "Pemasukan",
              "type": "income", "date": "2026-08-01"},
        headers=headers,
    )
    client.post(
        "/api/v1/transactions",
        json={"title": "Makan", "amount": 25000, "category": "Makanan",
              "type": "expense", "date": "2026-08-02"},
        headers=headers,
    )


def test_dashboard_requires_auth(client):
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 401


def test_dashboard_success(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get("/api/v1/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_income"] == 100000
    assert data["total_expense"] == 25000
    assert data["total_balance"] == 75000
    assert data["transaction_count"] == 2
    assert len(data["recent_transactions"]) == 2


def test_dashboard_scoped_to_user(client, auth_headers):
    _seed(client, auth_headers)

    from app.core.security import create_access_token

    other_token = create_access_token(
        subject="other-user",
        extra={"email": "other@example.com"},
    )
    other_headers = {"Authorization": f"Bearer {other_token}"}
    resp = client.get("/api/v1/dashboard", headers=other_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_income"] == 0
    assert data["transaction_count"] == 0
