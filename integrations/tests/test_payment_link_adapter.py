from decimal import Decimal
from unittest.mock import Mock
from uuid import uuid4

import pytest

from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryAdapter,
)


def make_mock_client() -> Mock:
    """
    Create a mocked Razorpay client wrapper.

    No real Razorpay API request is made.
    """

    mock_client = Mock()

    mock_client.client.payment_link.create.return_value = {
        "id": "plink_test_123",
        "short_url": "https://rzp.io/i/test-link",
        "status": "created",
        "amount": 50000,
        "currency": "INR",
    }

    return mock_client


def test_create_recovery_link_successfully() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    payment_id = uuid4()

    result = adapter.create_recovery_link(
        payment_id=payment_id,
        amount=Decimal("500.00"),
        currency="INR",
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

    assert result.amount == Decimal("500.00")

    assert result.currency == "INR"


def test_create_recovery_link_converts_inr_to_paise() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    payment_id = uuid4()

    adapter.create_recovery_link(
        payment_id=payment_id,
        amount=Decimal("250.50"),
    )

    payload = (
        mock_client
        .client
        .payment_link
        .create
        .call_args
        .args[0]
    )

    assert payload["amount"] == 25050


def test_create_recovery_link_uses_payment_id_as_reference() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    payment_id = uuid4()

    adapter.create_recovery_link(
        payment_id=payment_id,
        amount=Decimal("100.00"),
    )

    payload = (
        mock_client
        .client
        .payment_link
        .create
        .call_args
        .args[0]
    )

    assert (
        payload["reference_id"]
        == str(payment_id)
    )


def test_create_recovery_link_uses_default_description() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    adapter.create_recovery_link(
        payment_id=uuid4(),
        amount=Decimal("100.00"),
    )

    payload = (
        mock_client
        .client
        .payment_link
        .create
        .call_args
        .args[0]
    )

    assert (
        payload["description"]
        == "Payment recovery"
    )


def test_create_recovery_link_uses_custom_description() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    adapter.create_recovery_link(
        payment_id=uuid4(),
        amount=Decimal("100.00"),
        description="Recover failed subscription payment",
    )

    payload = (
        mock_client
        .client
        .payment_link
        .create
        .call_args
        .args[0]
    )

    assert (
        payload["description"]
        == "Recover failed subscription payment"
    )


def test_create_recovery_link_preserves_raw_response() -> None:
    mock_client = make_mock_client()

    adapter = PaymentLinkRecoveryAdapter(
        client=mock_client
    )

    result = adapter.create_recovery_link(
        payment_id=uuid4(),
        amount=Decimal("500.00"),
    )

    assert result.raw_response is not None

    assert (
        result.raw_response["id"]
        == "plink_test_123"
    )