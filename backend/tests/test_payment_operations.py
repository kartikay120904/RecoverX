from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def test_payment_operations_list():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    data = response.json()

    assert "payments" in data
    assert "total" in data
    assert isinstance(data["payments"], list)


def test_payment_operations_returns_payment_fields():
    response = client.get(
        "/recovery/payments",
        params={"limit": 5},
    )

    assert response.status_code == 200

    payments = response.json()["payments"]

    assert len(payments) > 0

    payment = payments[0]

    assert "payment_id" in payment
    assert "order_id" in payment
    assert "customer_id" in payment
    assert "merchant_id" in payment
    assert "amount" in payment
    assert "currency" in payment
    assert "method" in payment
    assert "status" in payment
    assert "failure_code" in payment


def test_payment_operations_search():
    response = client.get(
        "/recovery/payments",
        params={"search": "upi"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "payments" in data


def test_payment_operations_limit():
    response = client.get(
        "/recovery/payments",
        params={"limit": 3},
    )

    assert response.status_code == 200

    payments = response.json()["payments"]

    assert len(payments) <= 3


def test_payment_operations_invalid_payment():
    response = client.get(
        "/recovery/payments/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


def test_payment_operations_is_deterministic():
    first = client.get(
        "/recovery/payments",
        params={"limit": 10},
    )

    second = client.get(
        "/recovery/payments",
        params={"limit": 10},
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json() == second.json()