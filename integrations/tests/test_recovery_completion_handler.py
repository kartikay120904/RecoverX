from decimal import Decimal
from uuid import uuid4

from integrations.recovery.completion_handler import (
    RecoveryCompletionHandler,
    RecoveryCompletionResult,
)


def test_payment_link_paid_is_processed():
    """
    A completed Razorpay Payment Link recovery
    should be processed successfully.
    """

    payment_id = uuid4()

    handler = RecoveryCompletionHandler()

    result = handler.process(
        event_type="payment_link.paid",
        payment_link_id="plink_test_123",
        payment_id=str(payment_id),
        payment_status="paid",
        amount=50000,
    )

    assert isinstance(
        result,
        RecoveryCompletionResult,
    )

    assert result.processed is True

    assert result.payment_id == payment_id

    assert (
        result.payment_link_id
        == "plink_test_123"
    )

    assert result.payment_status == "paid"

    assert result.actual_revenue == Decimal(
        "500"
    )


def test_non_completion_event_is_not_processed():
    """
    Events other than payment_link.paid should
    not be treated as completed recoveries.
    """

    handler = RecoveryCompletionHandler()

    result = handler.process(
        event_type="payment_link.expired",
        payment_link_id="plink_test_expired",
        payment_id=None,
        payment_status="expired",
        amount=50000,
    )

    assert result.processed is False

    assert result.actual_revenue is None

    assert result.payment_id is None


def test_invalid_recoverx_payment_id_is_handled():
    """
    Invalid internal payment IDs should not crash
    webhook completion processing.
    """

    handler = RecoveryCompletionHandler()

    result = handler.process(
        event_type="payment_link.paid",
        payment_link_id="plink_test_invalid",
        payment_id="not-a-valid-uuid",
        payment_status="paid",
        amount=10000,
    )

    assert result.processed is True

    assert result.payment_id is None

    assert result.actual_revenue == Decimal(
        "100"
    )


def test_missing_amount_is_handled():
    """
    Missing amount should not crash processing.
    """

    handler = RecoveryCompletionHandler()

    result = handler.process(
        event_type="payment_link.paid",
        payment_link_id="plink_test_missing_amount",
        payment_id=None,
        payment_status="paid",
        amount=None,
    )

    assert result.processed is True

    assert result.actual_revenue is None