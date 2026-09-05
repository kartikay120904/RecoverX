from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.services.recovery_event_service import (
    RecoveryEventService,
)


def test_record_event_stores_event():
    service = RecoveryEventService()

    payment_id = uuid4()

    event = service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
        status=RecoveryStatus.PROPOSED,
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        details="Recovery strategy proposed.",
    )

    assert event.payment_id == payment_id

    assert event.event_type == "recovery_proposed"

    assert (
        event.status
        == RecoveryStatus.PROPOSED
    )

    assert (
        event.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_get_events_returns_payment_timeline():
    service = RecoveryEventService()

    payment_id = uuid4()

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
        status=RecoveryStatus.PROPOSED,
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_scheduled",
        status=RecoveryStatus.SCHEDULED,
    )

    events = service.get_events(
        payment_id,
    )

    assert len(events) == 2

    assert (
        events[0].event_type
        == "recovery_proposed"
    )

    assert (
        events[1].event_type
        == "recovery_scheduled"
    )


def test_get_latest_event_returns_last_event():
    service = RecoveryEventService()

    payment_id = uuid4()

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
    )

    latest = service.record_event(
        payment_id=payment_id,
        event_type="recovery_execution_started",
        status=RecoveryStatus.EXECUTING,
    )

    result = service.get_latest_event(
        payment_id,
    )

    assert result == latest

    assert (
        result.event_type
        == "recovery_execution_started"
    )


def test_get_latest_event_returns_none_for_unknown_payment():
    service = RecoveryEventService()

    result = service.get_latest_event(
        uuid4(),
    )

    assert result is None


def test_count_events_returns_correct_count():
    service = RecoveryEventService()

    payment_id = uuid4()

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_scheduled",
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_execution_started",
    )

    assert (
        service.count_events(
            payment_id,
        )
        == 3
    )


def test_iter_events_preserves_chronological_order():
    service = RecoveryEventService()

    payment_id = uuid4()

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_scheduled",
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_succeeded",
    )

    events = list(
        service.iter_events(
            payment_id,
        )
    )

    assert [
        event.event_type
        for event in events
    ] == [
        "recovery_proposed",
        "recovery_scheduled",
        "recovery_succeeded",
    ]


def test_events_are_isolated_between_payments():
    service = RecoveryEventService()

    first_payment_id = uuid4()

    second_payment_id = uuid4()

    service.record_event(
        payment_id=first_payment_id,
        event_type="recovery_proposed",
    )

    service.record_event(
        payment_id=second_payment_id,
        event_type="recovery_failed",
        status=RecoveryStatus.FAILED,
    )

    first_events = service.get_events(
        first_payment_id,
    )

    second_events = service.get_events(
        second_payment_id,
    )

    assert len(first_events) == 1

    assert len(second_events) == 1

    assert (
        first_events[0].payment_id
        == first_payment_id
    )

    assert (
        second_events[0].payment_id
        == second_payment_id
    )


def test_clear_events_removes_payment_timeline():
    service = RecoveryEventService()

    payment_id = uuid4()

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_proposed",
    )

    service.record_event(
        payment_id=payment_id,
        event_type="recovery_scheduled",
    )

    assert (
        service.count_events(
            payment_id,
        )
        == 2
    )

    service.clear_events(
        payment_id,
    )

    assert (
        service.count_events(
            payment_id,
        )
        == 0
    )

    assert (
        service.get_events(
            payment_id,
        )
        == []
    )