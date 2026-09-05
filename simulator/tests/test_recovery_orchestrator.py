from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
)

from backend.app.domain.models import Payment

from simulator.recovery.orchestrator import (
    RecoveryOrchestrator,
)


def make_failed_payment() -> Payment:

    return Payment(
        payment_id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000"),
        currency="INR",
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )


def test_proposal_creates_event():

    orchestrator = RecoveryOrchestrator()

    payment = make_failed_payment()

    attempt = orchestrator.propose(payment)

    assert attempt is not None

    events = orchestrator.get_events(
        payment.payment_id
    )

    assert len(events) == 1

    assert events[0].event_type == (
        "recovery_proposed"
    )

    assert events[0].status == (
        RecoveryStatus.PROPOSED
    )


def test_complete_recovery_workflow():

    orchestrator = RecoveryOrchestrator()

    payment = make_failed_payment()

    attempt = orchestrator.propose(payment)

    assert attempt is not None

    orchestrator.approve(attempt)
    orchestrator.schedule(attempt)
    orchestrator.start_execution(attempt)

    result = orchestrator.mark_succeeded(
        attempt
    )

    assert result.status == (
        RecoveryStatus.SUCCEEDED
    )

    assert result.actual_revenue == (
        result.predicted_revenue
    )

    events = orchestrator.get_events(
        payment.payment_id
    )

    assert len(events) == 5

    assert events[-1].event_type == (
        "recovery_succeeded"
    )


def test_failed_recovery_workflow():

    orchestrator = RecoveryOrchestrator()

    payment = make_failed_payment()

    attempt = orchestrator.propose(payment)

    assert attempt is not None

    orchestrator.approve(attempt)
    orchestrator.schedule(attempt)
    orchestrator.start_execution(attempt)

    result = orchestrator.mark_failed(
        attempt
    )

    assert result.status == (
        RecoveryStatus.FAILED
    )

    assert result.actual_revenue is None


def test_cancel_recovery():

    orchestrator = RecoveryOrchestrator()

    payment = make_failed_payment()

    attempt = orchestrator.propose(payment)

    assert attempt is not None

    result = orchestrator.cancel(attempt)

    assert result.status == (
        RecoveryStatus.CANCELLED
    )

    events = orchestrator.get_events(
        payment.payment_id
    )

    assert events[-1].event_type == (
        "recovery_cancelled"
    )