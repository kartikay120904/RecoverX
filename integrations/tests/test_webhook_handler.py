from decimal import Decimal

from integrations.recovery.webhook_handler import (
    RecoveryWebhookHandler,
)


def test_payment_link_paid_marks_recovery_completed():
    """
    A payment_link.paid event should be translated
    into a completed recovery.
    """

    handler = RecoveryWebhookHandler()

    payload = {
        "event": "payment_link.paid",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_test_123",
                    "status": "paid",
                    "amount": 50000,
                    "amount_paid": 50000,
                    "currency": "INR",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_test_123",
                    "status": "captured",
                }
            },
        },
    }

    result = handler.handle(
        payload
    )

    assert result.handled is True

    assert (
        result.recovery_completed
        is True
    )

    assert (
        result.payment_link_id
        == "plink_test_123"
    )

    assert (
        result.razorpay_payment_id
        == "pay_test_123"
    )

    assert (
        result.recovered_amount
        == Decimal("500")
    )

    assert result.currency == "INR"

    assert (
        result.event_type
        == "payment_link.paid"
    )


def test_non_recovery_event_is_ignored():
    """
    Events unrelated to payment link completion
    should not be marked as successful recovery.
    """

    handler = RecoveryWebhookHandler()

    payload = {
        "event": "payment.failed",
        "payload": {},
    }

    result = handler.handle(
        payload
    )

    assert result.handled is False

    assert (
        result.recovery_completed
        is False
    )

    assert (
        result.recovered_amount
        is None
    )

    assert result.currency is None