from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(
    app
)


def test_recovery_timeline_returns_response():

    payments_response = client.get(
        "/recovery/payments"
    )

    assert (
        payments_response.status_code
        == 200
    )

    data = (
        payments_response.json()
    )

    payments = (
        data["payments"]
    )

    assert len(
        payments
    ) > 0

    payment_id = (
        payments[0]["payment_id"]
    )

    response = client.get(
        f"/recovery/{payment_id}/timeline"
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        data["payment_id"]
        == payment_id
    )

    assert isinstance(
        data["timeline"],
        list,
    )

    assert (
        "total_events"
        in data
    )


def test_unknown_payment_timeline_returns_404():

    response = client.get(
        "/recovery/"
        "00000000-0000-0000-0000-000000000000"
        "/timeline"
    )

    assert (
        response.status_code
        == 404
    )