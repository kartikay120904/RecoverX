from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
)

from backend.app.services.recovery_lifecycle import (
    RecoveryLifecycleService,
)
from backend.app.domain.models import RecoveryAttempt
from backend.app.domain.models import Payment
from simulator.recovery.lifecycle import RecoveryLifecycle


def make_attempt() -> RecoveryAttempt:
    return RecoveryAttempt(
        recovery_id=uuid4(),
        payment_id=uuid4(),
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        predicted_probability=0.70,
        predicted_revenue=Decimal("700.00"),
        status=RecoveryStatus.PROPOSED,
    )


def test_approve_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    result = lifecycle.approve(attempt)

    assert result.status == RecoveryStatus.APPROVED


def test_reject_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    result = lifecycle.reject(attempt)

    assert result.status == RecoveryStatus.REJECTED


def test_schedule_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    lifecycle.approve(attempt)
    result = lifecycle.schedule(attempt)

    assert result.status == RecoveryStatus.SCHEDULED


def test_execute_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    lifecycle.approve(attempt)
    lifecycle.schedule(attempt)

    result = lifecycle.start_execution(attempt)

    assert result.status == RecoveryStatus.EXECUTING


def test_successful_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    lifecycle.approve(attempt)
    lifecycle.schedule(attempt)
    lifecycle.start_execution(attempt)

    result = lifecycle.mark_succeeded(attempt)

    assert result.status == RecoveryStatus.SUCCEEDED


def test_failed_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    lifecycle.approve(attempt)
    lifecycle.schedule(attempt)
    lifecycle.start_execution(attempt)

    result = lifecycle.mark_failed(attempt)

    assert result.status == RecoveryStatus.FAILED


def test_invalid_transition_raises_error():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    with pytest.raises(ValueError):
        lifecycle.schedule(attempt)


def test_cancel_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    result = lifecycle.cancel(attempt)

    assert result.status == RecoveryStatus.CANCELLED


def test_cannot_cancel_completed_recovery():
    lifecycle = RecoveryLifecycle()
    attempt = make_attempt()

    lifecycle.approve(attempt)
    lifecycle.schedule(attempt)
    lifecycle.start_execution(attempt)
    lifecycle.mark_succeeded(attempt)

    with pytest.raises(ValueError):
        lifecycle.cancel(attempt)

def test_complete_recovery_lifecycle():

    payment = Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.CARD,
        status=PaymentStatus.FAILED,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
        attempt_number=1,
    )

    service = RecoveryLifecycleService()

    result = service.recover(
        payment=payment,
    )

    assert result.attempt is not None

    assert result.attempt.status.value in {
        "succeeded",
        "failed",
    }

    timeline = service.get_timeline(
        payment,
    )

    assert len(timeline) >= 4

    assert (
        timeline[0].event_type
        == "recovery_proposed"
    )