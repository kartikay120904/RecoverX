from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


# =========================================================
# Health API
# =========================================================


def test_health_endpoint():
    """
    Verify that the RecoverX API health endpoint
    is reachable and returns the expected status.
    """

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "recoverx"


# =========================================================
# Simulation API
# =========================================================


def test_simulation_run():
    """
    Verify that a deterministic simulation can
    be executed successfully.
    """

    payload = {
        "seed": 42,
        "merchant_count": 2,
        "customers_per_merchant": 3,
        "orders_per_customer": 2,
    }

    response = client.post(
        "/simulation/run",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["merchants"] == 2
    assert data["customers"] == 6
    assert data["orders"] == 12

    assert data["payments"] >= 0
    assert data["events"] >= 0
    assert data["recovery_attempts"] >= 0


# =========================================================
# Analytics API
# =========================================================


def test_analytics_report():
    """
    Verify that analytics can be generated from
    a simulation run.
    """

    payload = {
        "seed": 42,
        "merchant_count": 2,
        "customers_per_merchant": 3,
        "orders_per_customer": 2,
    }

    response = client.post(
        "/analytics/report",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert "metrics" in data

    assert "success_rate_by_method" in data

    assert "failure_code_distribution" in data

    assert "failure_rate_by_merchant" in data

    assert (
        "failure_rate_by_customer_segment"
        in data
    )

    assert "anomalies" in data

    assert "incident" in data

    assert (
        "recovery_recommendations"
        in data
    )

    assert (
        "total_recovery_recommendations"
        in data
    )

    assert (
        "predicted_recovery_revenue"
        in data
    )


# =========================================================
# Razorpay Configuration API
# =========================================================


def test_razorpay_config():
    """
    Verify that the Razorpay public configuration
    endpoint exposes only the Test Mode key.
    """

    response = client.get(
        "/razorpay/config"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["mode"] == "test"

    assert data["key_id"].startswith(
        "rzp_test_"
    )


# =========================================================
# Razorpay Order Validation
# =========================================================


def test_razorpay_order_rejects_zero_amount():
    """
    Verify that invalid order amounts are rejected
    before calling Razorpay.
    """

    response = client.post(
        "/razorpay/order",
        json={
            "amount": 0,
            "currency": "INR",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "Amount must be greater than zero."
    )


def test_razorpay_order_rejects_negative_amount():
    """
    Verify that negative order amounts are rejected.
    """

    response = client.post(
        "/razorpay/order",
        json={
            "amount": -100,
            "currency": "INR",
        },
    )

    assert response.status_code == 400


def test_razorpay_order_rejects_non_inr_currency():
    """
    RecoverX currently supports INR only.
    """

    response = client.post(
        "/razorpay/order",
        json={
            "amount": 1000,
            "currency": "USD",
        },
    )

    assert response.status_code == 400

    data = response.json()

    assert (
        data["detail"]
        == "RecoverX currently supports INR only."
    )


# =========================================================
# Razorpay Verification Validation
# =========================================================


def test_razorpay_verify_rejects_invalid_signature():
    """
    Verify that an invalid payment signature
    is rejected.
    """

    response = client.post(
        "/razorpay/verify",
        json={
            "razorpay_order_id": (
                "order_invalid"
            ),
            "razorpay_payment_id": (
                "pay_invalid"
            ),
            "razorpay_signature": (
                "invalid_signature"
            ),
        },
    )

    assert response.status_code == 400


# =========================================================
# Unknown Route
# =========================================================


def test_unknown_route_returns_404():
    """
    Verify that an unknown endpoint is not
    accidentally exposed.
    """

    response = client.get(
        "/this-route-does-not-exist"
    )

    assert response.status_code == 404