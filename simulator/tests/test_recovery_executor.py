from decimal import Decimal
from random import Random
from uuid import uuid4

import pytest

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment, RecoveryAttempt
from simulator.recovery.executor import RecoveryExecutor


def make_payment() -> Payment:
    return Payment(
        payment_id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000"),
        currency="INR",
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=PaymentFailureCode.BANK_TIMEOUT.value,
    )


def make_attempt() -> RecoveryAttempt:
    return RecoveryAttempt(
        recovery_id=uuid4(),
        payment_id=uuid4(),
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        predicted_probability=0.70,
        predicted_revenue=Decimal("700"),
        status=RecoveryStatus.PROPOSED,
    )


def test_successful_recovery_records_actual_revenue():
    payment = make_payment()
    attempt = make_attempt()

    result = RecoveryExecutor().execute(
        attempt=attempt,
        payment=payment,
        rng=Random(1),
    )

    assert result.status == RecoveryStatus.SUCCEEDED
    assert result.actual_revenue == Decimal("1000")


def test_failed_recovery_records_zero_revenue():
    payment = make_payment()
    attempt = make_attempt()

    result = RecoveryExecutor().execute(
        attempt=attempt,
        payment=payment,
        rng=Random(0),
    )

    assert result.status == RecoveryStatus.FAILED
    assert result.actual_revenue == Decimal("0")


def test_only_proposed_attempt_can_be_executed():
    payment = make_payment()
    attempt = make_attempt()
    attempt.status = RecoveryStatus.SUCCEEDED

    with pytest.raises(
        ValueError,
        match="Only proposed recovery attempts can be executed",
    ):
        RecoveryExecutor().execute(
            attempt=attempt,
            payment=payment,
            rng=Random(1),
        )


def test_execution_is_deterministic_with_same_seed():
    payment = make_payment()

    first = RecoveryExecutor().execute(
        attempt=make_attempt(),
        payment=payment,
        rng=Random(42),
    )

    second = RecoveryExecutor().execute(
        attempt=make_attempt(),
        payment=payment,
        rng=Random(42),
    )

    assert first.status == second.status
    assert first.actual_revenue == second.actual_revenue