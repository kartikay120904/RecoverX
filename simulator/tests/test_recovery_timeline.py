from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from simulator.recovery.orchestrator import (
    RecoveryOrchestrator,
)


def make_attempt(
    payment_id,
) -> RecoveryAttempt:
    return RecoveryAttempt(
        payment_id=payment_id,
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        predicted_probability=0.7,
        predicted_revenue=Decimal("100.0"),
        status=RecoveryStatus.PROPOSED,
        reason="Test recovery attempt.",
    )


def test_recovery_timeline_contains_events_in_order():

    orchestrator = RecoveryOrchestrator()

    payment_id = uuid4()

    attempt = make_attempt(
        payment_id,
    )

    orchestrator._record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
        strategy=attempt.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Recovery proposed.",
    )

    orchestrator._record_event(
        payment_id=payment_id,
        event_type="recovery_approved",
        strategy=attempt.strategy,
        status=RecoveryStatus.APPROVED,
        details="Recovery approved.",
    )

    events = orchestrator.get_events(
        payment_id,
    )

    assert len(events) == 2

    assert events[0].event_type == (
        "recovery_proposed"
    )

    assert events[1].event_type == (
        "recovery_approved"
    )

    assert (
        events[0].timestamp
        <= events[1].timestamp
    )


def test_recovery_timeline_isolated_by_payment():

    orchestrator = RecoveryOrchestrator()

    payment_a = uuid4()
    payment_b = uuid4()

    attempt_a = make_attempt(
        payment_a,
    )

    attempt_b = make_attempt(
        payment_b,
    )

    orchestrator._record_event(
        payment_id=payment_a,
        event_type="recovery_proposed",
        strategy=attempt_a.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Payment A event.",
    )

    orchestrator._record_event(
        payment_id=payment_b,
        event_type="recovery_proposed",
        strategy=attempt_b.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Payment B event.",
    )

    events = orchestrator.get_events(
        payment_a,
    )

    assert len(events) == 1

    assert (
        events[0].payment_id
        == payment_a
    )


def test_returned_events_cannot_mutate_history():

    orchestrator = RecoveryOrchestrator()

    payment_id = uuid4()

    attempt = make_attempt(
        payment_id,
    )

    orchestrator._record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
        strategy=attempt.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Original event.",
    )

    events = orchestrator.get_events(
        payment_id,
    )

    events[0].event_type = "tampered"

    fresh_events = orchestrator.get_events(
        payment_id,
    )

    assert fresh_events[0].event_type == (
        "recovery_proposed"
    )


def test_get_all_events_returns_all_payments():

    orchestrator = RecoveryOrchestrator()

    payment_a = uuid4()
    payment_b = uuid4()

    attempt_a = make_attempt(
        payment_a,
    )

    attempt_b = make_attempt(
        payment_b,
    )

    orchestrator._record_event(
        payment_id=payment_a,
        event_type="recovery_proposed",
        strategy=attempt_a.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Payment A event.",
    )

    orchestrator._record_event(
        payment_id=payment_b,
        event_type="recovery_proposed",
        strategy=attempt_b.strategy,
        status=RecoveryStatus.PROPOSED,
        details="Payment B event.",
    )

    events = orchestrator.get_all_events()

    assert len(events) == 2

    payment_ids = {
        event.payment_id
        for event in events
    }

    assert payment_a in payment_ids
    assert payment_b in payment_ids


def test_recovery_event_metadata_is_preserved():

    orchestrator = RecoveryOrchestrator()

    payment_id = uuid4()

    attempt = make_attempt(
        payment_id,
    )

    orchestrator._record_event(
        payment_id=payment_id,
        event_type="recovery_failed",
        strategy=attempt.strategy,
        status=RecoveryStatus.FAILED,
        details="Recovery failed.",
        metadata={
            "execution_failures": 2,
        },
    )

    events = orchestrator.get_events(
        payment_id,
    )

    assert events[0].metadata == {
        "execution_failures": 2,
    }