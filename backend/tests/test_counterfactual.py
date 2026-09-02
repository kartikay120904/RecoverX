from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def test_counterfactual_analysis_returns_options():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    payment_id = failed_payment["payment_id"]

    response = client.get(
        f"/recovery/{payment_id}/counterfactual"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["payment_id"] == payment_id
    assert "recommended_strategy" in data
    assert "options" in data

    assert len(data["options"]) == 6


def test_counterfactual_options_are_bounded():
    response = client.get("/recovery/payments")

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    response = client.get(
        f"/recovery/{failed_payment['payment_id']}/counterfactual"
    )

    assert response.status_code == 200

    for option in response.json()["options"]:
        assert 0 <= option["probability"] <= 0.95
        assert 0 <= option["relative_uplift"] <= 1


def test_counterfactual_invalid_payment():
    response = client.get(
        "/recovery/"
        "00000000-0000-0000-0000-000000000000"
        "/counterfactual"
    )

    assert response.status_code == 404

