from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.models import Payment
from app.domain.state_machine import (
    InvalidPaymentTransition,
    transition_payment,
)


def create_payment() -> Payment:
    return Payment(
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("2499.00"),
        method=PaymentMethod.UPI,
    )


def test_created_to_authorized_is_valid():
    payment = create_payment()

    event = transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    assert payment.status == PaymentStatus.AUTHORIZED
    assert event.event_type == "payment.status_changed"
    assert event.payload["previous_status"] == "created"
    assert event.payload["new_status"] == "authorized"


def test_authorized_to_captured_is_valid():
    payment = create_payment()

    transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    transition_payment(
        payment,
        PaymentStatus.CAPTURED,
        actor="payment_service",
    )

    assert payment.status == PaymentStatus.CAPTURED


def test_created_to_captured_is_invalid():
    payment = create_payment()

    with pytest.raises(InvalidPaymentTransition):
        transition_payment(
            payment,
            PaymentStatus.CAPTURED,
            actor="ai_agent",
        )


def test_captured_to_captured_is_invalid():
    payment = create_payment()

    transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    transition_payment(
        payment,
        PaymentStatus.CAPTURED,
        actor="payment_service",
    )

    with pytest.raises(InvalidPaymentTransition):
        transition_payment(
            payment,
            PaymentStatus.CAPTURED,
            actor="ai_agent",
        )


def test_refunded_is_terminal():
    payment = create_payment()

    transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    transition_payment(
        payment,
        PaymentStatus.CAPTURED,
        actor="payment_service",
    )

    transition_payment(
        payment,
        PaymentStatus.REFUNDED,
        actor="payment_service",
    )

    with pytest.raises(InvalidPaymentTransition):
        transition_payment(
            payment,
            PaymentStatus.CAPTURED,
            actor="payment_service",
        )