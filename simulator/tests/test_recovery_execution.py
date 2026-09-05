from decimal import Decimal

import pytest

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)
from backend.app.services.recovery_execution import (
    can_transition,
    execute_recovery,
    schedule_recovery,
)


def create_payment():

    return Payment(
        amount=Decimal("10000"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )


def create_attempt(
    probability=0.8,
):

    payment = create_payment()

    return payment, RecoveryAttempt(
        payment_id=payment.payment_id,
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        predicted_probability=probability,
        predicted_revenue=(
            Decimal("8000")
        ),
    )


def test_valid_lifecycle_transition():

    assert can_transition(
        RecoveryStatus.PROPOSED,
        RecoveryStatus.SCHEDULED,
    )


def test_invalid_lifecycle_transition():

    assert not can_transition(
        RecoveryStatus.PROPOSED,
        RecoveryStatus.SUCCEEDED,
    )


def test_recovery_execution_succeeds():

    payment, attempt = create_attempt(
        probability=0.8,
    )

    result = execute_recovery(
        payment,
        attempt,
    )

    assert (
        result.attempt.status
        == RecoveryStatus.SUCCEEDED
    )

    assert (
        result.attempt.actual_revenue
        == payment.amount
    )


def test_recovery_execution_fails():

    payment, attempt = create_attempt(
        probability=0.2,
    )

    result = execute_recovery(
        payment,
        attempt,
    )

    assert (
        result.attempt.status
        == RecoveryStatus.FAILED
    )

    assert (
        result.attempt.actual_revenue
        == Decimal("0")
    )


def test_execution_creates_events():

    payment, attempt = create_attempt(
        probability=0.8,
    )

    result = execute_recovery(
        payment,
        attempt,
    )

    assert len(result.events) == 3

    assert (
        result.events[0].event_type
        == "recovery_scheduled"
    )

    assert (
        result.events[1].event_type
        == "recovery_execution_started"
    )

    assert (
        result.events[2].event_type
        == "recovery_succeeded"
    )


def test_execution_is_deterministic():

    payment1, attempt1 = create_attempt(
        probability=0.8,
    )

    payment2, attempt2 = create_attempt(
        probability=0.8,
    )

    result1 = execute_recovery(
        payment1,
        attempt1,
    )

    result2 = execute_recovery(
        payment2,
        attempt2,
    )

    assert (
        result1.attempt.status
        == result2.attempt.status
    )

    assert (
        result1.attempt.actual_revenue
        == result2.attempt.actual_revenue
    )


def test_invalid_schedule_raises():

    payment, attempt = create_attempt()

    attempt.status = (
        RecoveryStatus.SUCCEEDED
    )

    with pytest.raises(
        ValueError,
    ):
        schedule_recovery(
            attempt,
        )