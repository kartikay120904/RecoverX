from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def test_adaptive_decision_returns_success():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    assert payments

    payment_id = payments[0]["payment_id"]

    decision_response = client.get(
        f"/recovery/{payment_id}/decision"
    )

    assert decision_response.status_code == 200

    data = decision_response.json()

    assert data["payment_id"] == payment_id
    assert "strategy" in data
    assert "confidence" in data
    assert "priority_score" in data
    assert "predicted_probability" in data
    assert "predicted_revenue" in data
    assert "timing" in data
    assert "explanation" in data
    assert "signals" in data


def test_adaptive_decision_confidence_is_bounded():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    for payment in payments[:10]:
        decision_response = client.get(
            f"/recovery/{payment['payment_id']}/decision"
        )

        assert decision_response.status_code == 200

        decision = decision_response.json()

        assert 0 <= decision["confidence"] <= 1
        assert 0 <= decision["priority_score"] <= 1
        assert 0 <= decision["predicted_probability"] <= 1


def test_adaptive_decision_is_deterministic():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    assert payments

    payment_id = payments[0]["payment_id"]

    first = client.get(
        f"/recovery/{payment_id}/decision"
    )

    second = client.get(
        f"/recovery/{payment_id}/decision"
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert first.json() == second.json()


def test_adaptive_decision_invalid_payment():
    response = client.get(
        "/recovery/"
        "00000000-0000-0000-0000-000000000000"
        "/decision"
    )

    assert response.status_code == 404