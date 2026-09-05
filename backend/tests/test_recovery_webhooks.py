from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(
    app
)


def test_recovery_webhook_history():

    response = client.get(
        "/recovery/webhooks"
    )

    assert (
        response.status_code
        == 200
    )

    data = response.json()

    assert (
        "total"
        in data
    )

    assert isinstance(
        data["webhooks"],
        list,
    )