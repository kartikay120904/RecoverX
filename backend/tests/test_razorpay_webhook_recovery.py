import hashlib
import hmac
import json
import os

from fastapi.testclient import TestClient

from backend.app.api.main import app
from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt
)
from integrations.recovery.payment_link_store import (
    payment_link_store,
)
from integrations.recovery.recovery_store import (
    recovery_store,
)


client = TestClient(app)


def create_signature(
    raw_body: bytes,
) -> str:
    """
    Create a valid webhook signature using the
    configured local test webhook secret.
    """

    webhook_secret = os.getenv(
        "RAZORPAY_WEBHOOK_SECRET"
    )

    assert webhook_secret is not None

    return hmac.new(
        webhook_secret.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def test_verified_payment_link_paid_completes_recovery():
    """
    A valid payment_link.paid webhook should be
    verified and translated into a completed
    recovery outcome.
    """

    # -------------------------------------------------
    # Arrange: create an internal RecoverX payment
    # -------------------------------------------------

    internal_payment_id = uuid4()

    recovery_attempt = RecoveryAttempt(
        payment_id=internal_payment_id,
        strategy=RecoveryStrategy.RECOVERY_LINK,
        predicted_probability=0.80,
        predicted_revenue=Decimal("500.00"),
        status=RecoveryStatus.EXECUTING,
    )

    recovery_store.register_attempt(
        recovery_attempt
    )

    # -------------------------------------------------
    # Map Razorpay Payment Link -> RecoverX payment
    # -------------------------------------------------

    payment_link_store.register(
        payment_link_id="plink_test_recovery",
        payment_id=internal_payment_id,
    )

    # -------------------------------------------------
    # Razorpay webhook payload
    # -------------------------------------------------

    payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_recovery",
                    "status": "paid",
                    "amount": 50000,
                    "amount_paid": 50000,
                    "currency": "INR",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_recovery",
                    "status": "captured",
                }
            },
        },
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode()

    signature = create_signature(
        raw_body
    )

    # -------------------------------------------------
    # Act
    # -------------------------------------------------

    response = client.post(
        "/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )

    # -------------------------------------------------
    # Assert webhook response
    # -------------------------------------------------

    assert response.status_code == 200

    data = response.json()

    assert data["received"] is True

    assert data["verified"] is True

    assert (
        data["event_type"]
        == "payment_link.paid"
    )

    assert data["handled"] is True

    assert (
        data["recovery_completed"]
        is True
    )

    assert (
        data["payment_link_id"]
        == "plink_test_recovery"
    )

    assert (
        data["razorpay_payment_id"]
        == "pay_test_recovery"
    )

    assert (
        data["recovered_amount"]
        == "500"
    )

    assert data["currency"] == "INR"

    # -------------------------------------------------
    # Assert internal recovery lifecycle
    # -------------------------------------------------

    persisted_attempt = (
        recovery_store.get_attempt(
            internal_payment_id
        )
    )

    assert persisted_attempt is not None

    assert (
        persisted_attempt.status
        == RecoveryStatus.SUCCEEDED
    )

    assert (
        persisted_attempt.actual_revenue
        == Decimal("500")
    )