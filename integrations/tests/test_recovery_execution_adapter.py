from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryResult,
)
from integrations.recovery.execution_adapter import (
    RecoveryExecutionAdapter,
    RecoveryExecutionResult,
)


def test_execution_adapter_creates_payment_link():
    """
    Verify that a recovery execution delegates to
    the Razorpay Payment Link adapter.
    """

    payment_id = uuid4()

    mock_payment_link_adapter = Mock()

    mock_payment_link_adapter.create_recovery_link.return_value = (
        PaymentLinkRecoveryResult(
            success=True,
            payment_link_id="plink_test_123",
            short_url="https://rzp.io/i/test-link",
            status="created",
            amount=Decimal("500.00"),
            currency="INR",
            raw_response={
                "id": "plink_test_123",
                "status": "created",
            },
        )
    )

    adapter = RecoveryExecutionAdapter(
        payment_link_adapter=mock_payment_link_adapter
    )

    result = adapter.execute(
        payment_id=payment_id,
        amount=Decimal("500.00"),
        currency="INR",
        description="Recover failed payment",
    )

    assert isinstance(
        result,
        RecoveryExecutionResult,
    )

    assert result.success is True

    assert (
        result.payment_link_id
        == "plink_test_123"
    )

    assert (
        result.short_url
        == "https://rzp.io/i/test-link"
    )

    assert result.status == "created"

    assert result.amount == Decimal(
        "500.00"
    )

    assert result.currency == "INR"

    mock_payment_link_adapter.create_recovery_link.assert_called_once_with(
        payment_id=payment_id,
        amount=Decimal("500.00"),
        currency="INR",
        description="Recover failed payment",
    )


def test_execution_adapter_preserves_failed_result():
    """
    Verify that a failed execution result is
    propagated correctly.
    """

    payment_id = uuid4()

    mock_payment_link_adapter = Mock()

    mock_payment_link_adapter.create_recovery_link.return_value = (
        PaymentLinkRecoveryResult(
            success=False,
            payment_link_id=None,
            short_url=None,
            status="failed",
            amount=Decimal("250.00"),
            currency="INR",
            raw_response=None,
        )
    )

    adapter = RecoveryExecutionAdapter(
        payment_link_adapter=mock_payment_link_adapter
    )

    result = adapter.execute(
        payment_id=payment_id,
        amount=Decimal("250.00"),
        currency="INR",
    )

    assert result.success is False

    assert result.payment_link_id is None

    assert result.short_url is None

    assert result.status == "failed"

    assert result.amount == Decimal(
        "250.00"
    )

    assert result.currency == "INR"


def test_execution_adapter_uses_default_description():
    """
    Verify that the execution adapter can execute
    without explicitly supplying a description.
    """

    payment_id = uuid4()

    mock_payment_link_adapter = Mock()

    mock_payment_link_adapter.create_recovery_link.return_value = (
        PaymentLinkRecoveryResult(
            success=True,
            payment_link_id="plink_test_default",
            short_url="https://rzp.io/i/default",
            status="created",
            amount=Decimal("100.00"),
            currency="INR",
            raw_response={},
        )
    )

    adapter = RecoveryExecutionAdapter(
        payment_link_adapter=mock_payment_link_adapter
    )

    result = adapter.execute(
        payment_id=payment_id,
        amount=Decimal("100.00"),
    )

    assert result.success is True

    mock_payment_link_adapter.create_recovery_link.assert_called_once()

    call_kwargs = (
        mock_payment_link_adapter
        .create_recovery_link
        .call_args
        .kwargs
    )

    assert (
        call_kwargs["payment_id"]
        == payment_id
    )

    assert (
        call_kwargs["amount"]
        == Decimal("100.00")
    )

    assert (
        call_kwargs["currency"]
        == "INR"
    )