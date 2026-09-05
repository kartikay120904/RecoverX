import hashlib
import hmac
import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def create_signature(
    *,
    secret: str,
    body: bytes,
) -> str:
    """
    Create a Razorpay-compatible HMAC SHA256
    signature for webhook testing.
    """

    return hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()


def test_webhook_rejects_missing_signature():
    """
    Webhook requests without the Razorpay
    signature must be rejected.
    """

    response = client.post(
        "/webhooks/razorpay",
        json={
            "event": "payment_link.paid",
            "payload": {},
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Missing X-Razorpay-Signature header"
    )


def test_webhook_rejects_invalid_signature():
    """
    An invalid Razorpay webhook signature must
    not be accepted.
    """

    payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_123",
                    "status": "paid",
                }
            }
        },
    }

    response = client.post(
        "/webhooks/razorpay",
        json=payload,
        headers={
            "X-Razorpay-Signature": (
                "invalid_signature"
            )
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Invalid Razorpay webhook signature"
    )