import hashlib
import hmac
import json
import os

from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def create_signature(
    payload: dict,
    secret: str,
) -> str:
    """
    Create a valid Razorpay-style webhook
    signature for testing.
    """

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    return hmac.new(
        secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def test_payment_link_paid_processes_recovery(
    monkeypatch,
):
    """
    A verified payment_link.paid event should
    process recovery completion.
    """

    webhook_secret = "test_webhook_secret"

    monkeypatch.setenv(
        "RAZORPAY_WEBHOOK_SECRET",
        webhook_secret,
    )

    payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_123",
                    "status": "paid",
                    "amount": 50000,
                    "reference_id": (
                        "550e8400-e29b-41d4-a716-"
                        "446655440000"
                    ),
                }
            }
        },
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = hmac.new(
        webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["received"] is True
    assert data["verified"] is True
    assert data["event_type"] == "payment_link.paid"

    assert data["recovery_processed"] is True

    assert data["actual_revenue"] == "500"


def test_non_paid_event_does_not_process_recovery(
    monkeypatch,
):
    """
    A verified event other than payment_link.paid
    should not complete a recovery.
    """

    webhook_secret = "test_webhook_secret"

    monkeypatch.setenv(
        "RAZORPAY_WEBHOOK_SECRET",
        webhook_secret,
    )

    payload = {
        "event": "payment_link.expired",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_expired",
                    "status": "expired",
                    "amount": 50000,
                }
            }
        },
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = hmac.new(
        webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    response = client.post(
        "/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["verified"] is True

    assert data["recovery_processed"] is False

    assert data["actual_revenue"] is None