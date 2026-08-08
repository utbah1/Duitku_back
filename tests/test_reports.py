"""Report tests."""


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
    client.post(
        "/api/v1/transactions",
        json={"title": "Transport", "amount": 15000, "category": "Transport",
              "type": "expense", "date": "2026-08-03"},
        headers=headers,
    )


def test_summary_report(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get("/api/v1/reports/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_income"] == 100000
    assert data["total_expense"] == 40000
    assert data["balance"] == 60000
    assert data["transaction_count"] == 3


def test_monthly_report(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get(
        "/api/v1/reports/monthly?year=2026&month=8", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["total_income"] == 100000
    assert data["total_expense"] == 40000
    assert data["balance"] == 60000
    assert data["transaction_count"] == 3


def test_monthly_report_empty_for_other_month(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get(
        "/api/v1/reports/monthly?year=2026&month=1", headers=auth_headers
    )
    data = resp.json()["data"]
    assert data["total_income"] == 0
    assert data["transaction_count"] == 0


def test_weekly_report_structure(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get("/api/v1/reports/weekly", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data["days"]) == 7
    # Days are Senin..Minggu
    expected = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    assert [d["day"] for d in data["days"]] == expected


def test_category_report(client, auth_headers):
    _seed(client, auth_headers)
    resp = client.get(
        "/api/v1/reports/categories?type=expense", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    totals = {item["category"]: item["total"] for item in data}
    assert totals["Makanan"] == 25000
    assert totals["Transport"] == 15000
    # Percentages should sum to ~100
    total_pct = round(sum(item["percentage"] for item in data), 1)
    assert total_pct == 100.0
