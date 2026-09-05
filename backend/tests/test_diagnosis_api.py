from fastapi.testclient import TestClient

from backend.app.api.main import app

client = TestClient(app)

def _get_failed_payment():
    response = client.get(
        "/recovery/payments"
    )

    assert response.status_code == 200

    payments = response.json()[
        "payments"
    ]

    return next(
        payment
        for payment in payments
        if payment["failure_code"]
        is not None
    )


def test_payment_diagnosis_returns_result():

    payment = _get_failed_payment()

    response = client.get(
        f"/recovery/"
        f"{payment['payment_id']}"
        f"/diagnosis"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["payment_id"]
        == payment["payment_id"]
    )

    assert "diagnosis" in data

    diagnosis = data[
        "diagnosis"
    ]

    assert "category" in diagnosis

    assert "root_cause" in diagnosis

    assert (
        "recommended_strategy"
        in diagnosis
    )

    assert (
        "confidence"
        in diagnosis
    )


def test_failed_payment_has_recovery_strategy():

    payment = _get_failed_payment()

    response = client.get(
        f"/recovery/"
        f"{payment['payment_id']}"
        f"/diagnosis"
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data[
            "final_recommended_strategy"
        ]
        is not None
    )

    assert (
        0.0
        <= data["diagnosis"]["confidence"]
        <= 1.0
    )


def test_unknown_payment_returns_404():

    response = client.get(
        "/recovery/"
        "11111111-1111-1111-1111-111111111111"
        "/diagnosis"
    )

    assert response.status_code == 404