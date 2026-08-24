from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "recoverx",
    }


def test_simulation_run_endpoint():
    response = client.post(
        "/simulation/run",
        json={
            "seed": 42,
            "merchant_count": 4,
            "customers_per_merchant": 10,
            "orders_per_customer": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["merchants"] == 4
    assert data["customers"] == 40
    assert data["orders"] == 200
    assert data["payments"] == 200
    assert "events" in data
    assert "recovery_attempts" in data


def test_analytics_report_endpoint():
    response = client.post(
        "/analytics/report",
        json={
            "seed": 42,
            "merchant_count": 4,
            "customers_per_merchant": 10,
            "orders_per_customer": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "metrics" in data
    assert "success_rate_by_method" in data
    assert "failure_code_distribution" in data
    assert "failure_rate_by_merchant" in data
    assert "failure_rate_by_customer_segment" in data
    assert "anomalies" in data
    assert "incident" in data
    assert "recovery_recommendations" in data


def test_analytics_report_contains_metrics():
    response = client.post(
        "/analytics/report",
        json={
            "seed": 42,
            "merchant_count": 4,
            "customers_per_merchant": 10,
            "orders_per_customer": 5,
        },
    )

    data = response.json()
    metrics = data["metrics"]

    assert metrics["total_payments"] == 200
    assert metrics["successful_payments"] >= 0
    assert metrics["failed_payments"] >= 0

    assert (
        metrics["successful_payments"]
        + metrics["failed_payments"]
        == metrics["total_payments"]
    )


def test_analytics_report_is_deterministic():
    config = {
        "seed": 42,
        "merchant_count": 4,
        "customers_per_merchant": 10,
        "orders_per_customer": 5,
    }

    first = client.post(
        "/analytics/report",
        json=config,
    ).json()

    second = client.post(
        "/analytics/report",
        json=config,
    ).json()

    assert first == second