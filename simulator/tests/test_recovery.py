from decimal import Decimal
from random import Random
from uuid import uuid4

import pytest

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from backend.app.domain.state_machine import (
    InvalidPaymentTransition,
    InvalidRecoveryTransition,
    transition_payment,
    transition_recovery,
)

from simulator.recovery.executor import (
    RecoveryExecutor,
)


# =========================================================
# Helpers
# =========================================================


def create_payment() -> Payment:

    return Payment(
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000.00"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.CREATED,
    )


def create_recovery_attempt(
    payment_id,
    probability: float = 0.8,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        payment_id=payment_id,
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        predicted_probability=probability,
        predicted_revenue=Decimal("1000.00"),
    )


# =========================================================
# Payment State Machine Tests
# =========================================================


def test_payment_created_to_authorized():

    payment = create_payment()

    event = transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="test",
    )

    assert payment.status == PaymentStatus.AUTHORIZED

    assert event.event_type == (
        "payment.status_changed"
    )

    assert event.entity_id == (
        payment.payment_id
    )

    assert event.payload[
        "previous_status"
    ] == "created"

    assert event.payload[
        "new_status"
    ] == "authorized"


def test_invalid_payment_transition():

    payment = create_payment()

    with pytest.raises(
        InvalidPaymentTransition
    ):

        transition_payment(
            payment,
            PaymentStatus.CAPTURED,
            actor="test",
        )


def test_payment_failure_to_retry():

    payment = create_payment()

    transition_payment(
        payment,
        PaymentStatus.FAILED,
        actor="test",
    )

    assert payment.status == (
        PaymentStatus.FAILED
    )

    transition_payment(
        payment,
        PaymentStatus.RETRY_ELIGIBLE,
        actor="test",
    )

    assert payment.status == (
        PaymentStatus.RETRY_ELIGIBLE
    )

    transition_payment(
        payment,
        PaymentStatus.RETRYING,
        actor="test",
    )

    assert payment.status == (
        PaymentStatus.RETRYING
    )


# =========================================================
# Recovery State Machine Tests
# =========================================================


def test_recovery_proposed_to_approved():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id
    )

    event = transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    assert attempt.status == (
        RecoveryStatus.APPROVED
    )

    assert event.event_type == (
        "recovery.status_changed"
    )

    assert event.entity_id == (
        payment.payment_id
    )

    assert event.payload[
        "previous_status"
    ] == "proposed"

    assert event.payload[
        "new_status"
    ] == "approved"


def test_invalid_recovery_transition():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id
    )

    with pytest.raises(
        InvalidRecoveryTransition
    ):

        transition_recovery(
            attempt,
            RecoveryStatus.SUCCEEDED,
        )


def test_recovery_full_lifecycle():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id
    )

    # PROPOSED -> APPROVED

    transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    assert attempt.status == (
        RecoveryStatus.APPROVED
    )

    # APPROVED -> EXECUTING

    transition_recovery(
        attempt,
        RecoveryStatus.EXECUTING,
    )

    assert attempt.status == (
        RecoveryStatus.EXECUTING
    )

    # EXECUTING -> SUCCEEDED

    transition_recovery(
        attempt,
        RecoveryStatus.SUCCEEDED,
    )

    assert attempt.status == (
        RecoveryStatus.SUCCEEDED
    )


# =========================================================
# Recovery Executor Tests
# =========================================================


def test_recovery_executor_success():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id,
        probability=1.0,
    )

    transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    executor = RecoveryExecutor()

    rng = Random(42)

    result = executor.execute(
        attempt=attempt,
        payment=payment,
        rng=rng,
    )

    assert result.status == (
        RecoveryStatus.SUCCEEDED
    )

    assert result.actual_revenue == (
        payment.amount
    )


def test_recovery_executor_failure():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id,
        probability=0.0,
    )

    transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    executor = RecoveryExecutor()

    rng = Random(42)

    result = executor.execute(
        attempt=attempt,
        payment=payment,
        rng=rng,
    )

    assert result.status == (
        RecoveryStatus.FAILED
    )

    assert result.actual_revenue == (
        Decimal("0")
    )


# =========================================================
# Deterministic Probability Tests
# =========================================================


def test_probability_one_always_succeeds():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id,
        probability=1.0,
    )

    transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    executor = RecoveryExecutor()

    rng = Random(123)

    result = executor.execute(
        attempt,
        payment,
        rng,
    )

    assert result.status == (
        RecoveryStatus.SUCCEEDED
    )


def test_probability_zero_always_fails():

    payment = create_payment()

    attempt = create_recovery_attempt(
        payment.payment_id,
        probability=0.0,
    )

    transition_recovery(
        attempt,
        RecoveryStatus.APPROVED,
    )

    executor = RecoveryExecutor()

    rng = Random(123)

    result = executor.execute(
        attempt,
        payment,
        rng,
    )

    assert result.status == (
        RecoveryStatus.FAILED
    )