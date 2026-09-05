import hashlib
import hmac
import json

import pytest

from integrations.recovery.webhook_verifier import (
    RazorpayWebhookVerifier,
)


WEBHOOK_SECRET = (
    "test_webhook_secret"
)


def create_signature(
    raw_body: bytes,
) -> str:
    """
    Create a valid Razorpay-style webhook
    signature for testing.
    """

    return hmac.new(
        WEBHOOK_SECRET.encode(
            "utf-8"
        ),
        raw_body,
        hashlib.sha256,
    ).hexdigest()


def create_payload() -> dict:
    """
    Representative Payment Link paid event.
    """

    return {
        "entity": "event",
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": (
                        "plink_test_123"
                    ),
                    "status": "paid",
                    "amount": 50000,
                    "currency": "INR",
                }
            },
            "payment": {
                "entity": {
                    "id": (
                        "pay_test_123"
                    ),
                }
            },
        },
    }


def test_valid_webhook_signature_is_verified():

    verifier = (
        RazorpayWebhookVerifier(
            webhook_secret=WEBHOOK_SECRET
        )
    )

    payload = create_payload()

    raw_body = json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    signature = create_signature(
        raw_body
    )

    assert (
        verifier.verify_signature(
            raw_body=raw_body,
            signature=signature,
        )
        is True
    )


def test_invalid_webhook_signature_is_rejected():

    verifier = (
        RazorpayWebhookVerifier(
            webhook_secret=WEBHOOK_SECRET
        )
    )

    payload = create_payload()

    raw_body = json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    assert (
        verifier.verify_signature(
            raw_body=raw_body,
            signature=(
                "invalid_signature"
            ),
        )
        is False
    )


def test_paid_payment_link_webhook_is_processed():

    verifier = (
        RazorpayWebhookVerifier(
            webhook_secret=WEBHOOK_SECRET
        )
    )

    payload = create_payload()

    raw_body = json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    signature = create_signature(
        raw_body
    )

    result = verifier.process(
        raw_body=raw_body,
        signature=signature,
        payload=payload,
    )

    assert result.verified is True

    assert (
        result.event_type
        == "payment_link.paid"
    )

    assert (
        result.payment_link_id
        == "plink_test_123"
    )

    assert (
        result.payment_id
        == "pay_test_123"
    )

    assert (
        result.payment_status
        == "paid"
    )

    assert result.amount == 50000

    assert result.currency == "INR"


def test_invalid_webhook_is_not_processed():

    verifier = (
        RazorpayWebhookVerifier(
            webhook_secret=WEBHOOK_SECRET
        )
    )

    payload = create_payload()

    raw_body = json.dumps(
        payload,
        separators=(
            ",",
            ":",
        ),
    ).encode(
        "utf-8"
    )

    result = verifier.process(
        raw_body=raw_body,
        signature=(
            "invalid_signature"
        ),
        payload=payload,
    )

    assert result.verified is False

    assert result.event_type is None

    assert result.payment_link_id is None

    assert result.payment_id is None

    assert result.raw_payload is None


def test_missing_webhook_secret_raises_error():

    with pytest.raises(
        RuntimeError,
        match=(
            "RAZORPAY_WEBHOOK_SECRET "
            "is not configured"
        ),
    ):

        RazorpayWebhookVerifier(
            webhook_secret=""
        )