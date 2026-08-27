from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.api.main import app
from backend.app.api.recovery import (
    payments_store,
    recovery_store,
)


client = TestClient(app)


def setup_function():
    payments_store.clear()
    recovery_store.clear()


def test_get_recommendations():
    response = client.get("/recovery/recommendations")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    recommendation = data[0]

    assert "recovery_id" in recommendation
    assert "payment_id" in recommendation
    assert "strategy" in recommendation
    assert "predicted_probability" in recommendation
    assert "predicted_revenue" in recommendation
    assert recommendation["status"] == "proposed"


def test_get_single_recovery():
    response = client.get("/recovery/recommendations")

    assert response.status_code == 200

    recommendations = response.json()

    payment_id = recommendations[0]["payment_id"]

    response = client.get(
        f"/recovery/{payment_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id


def test_approve_recovery():
    response = client.get("/recovery/recommendations")

    recommendations = response.json()

    payment_id = recommendations[0]["payment_id"]

    response = client.post(
        f"/recovery/{payment_id}/approve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id
    assert data["status"] == "approved"
    assert "strategy" in data
    assert "predicted_probability" in data
    assert "predicted_revenue" in data


def test_execute_requires_approval():
    response = client.get("/recovery/recommendations")

    recommendations = response.json()

    payment_id = recommendations[0]["payment_id"]

    response = client.post(
        f"/recovery/{payment_id}/execute"
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Recovery must be approved before execution."
    )


def test_approve_then_execute():
    response = client.get("/recovery/recommendations")

    recommendations = response.json()

    payment_id = recommendations[0]["payment_id"]

    approve_response = client.post(
        f"/recovery/{payment_id}/approve"
    )

    assert approve_response.status_code == 200

    execute_response = client.post(
        f"/recovery/{payment_id}/execute"
    )

    assert execute_response.status_code == 200

    data = execute_response.json()

    assert data["payment_id"] == payment_id
    assert data["status"] in {
        "succeeded",
        "failed",
    }

    assert "actual_revenue" in data


def test_invalid_payment_returns_404():
    fake_payment_id = UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    response = client.get(
        f"/recovery/{fake_payment_id}"
    )

    assert response.status_code == 404