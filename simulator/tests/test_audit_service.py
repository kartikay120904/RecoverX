from uuid import uuid4

from backend.app.domain.audit import (
    AuditEventType,
)

from simulator.audit.service import (
    AuditService,
)


def test_record_creates_event():

    service = AuditService()

    payment_id = uuid4()
    recovery_id = uuid4()

    event = service.record(
        event_type=(
            AuditEventType.RECOVERY_PROPOSED
        ),
        payment_id=payment_id,
        recovery_id=recovery_id,
    )

    assert event.event_type == (
        AuditEventType.RECOVERY_PROPOSED
    )

    assert event.payment_id == payment_id

    assert event.recovery_id == recovery_id


def test_record_increases_count():

    service = AuditService()

    service.record(
        AuditEventType.PAYMENT_DETECTED
    )

    service.record(
        AuditEventType.RECOVERY_PROPOSED
    )

    assert service.count() == 2


def test_all_events_returns_events():

    service = AuditService()

    first_event = service.record(
        AuditEventType.PAYMENT_DETECTED
    )

    second_event = service.record(
        AuditEventType.RECOVERY_PROPOSED
    )

    events = service.all_events()

    assert len(events) == 2

    assert events[0] == first_event

    assert events[1] == second_event


def test_events_for_payment():

    service = AuditService()

    first_payment_id = uuid4()

    second_payment_id = uuid4()

    service.record(
        AuditEventType.PAYMENT_DETECTED,
        payment_id=first_payment_id,
    )

    service.record(
        AuditEventType.RECOVERY_PROPOSED,
        payment_id=first_payment_id,
    )

    service.record(
        AuditEventType.PAYMENT_DETECTED,
        payment_id=second_payment_id,
    )

    events = service.events_for_payment(
        first_payment_id
    )

    assert len(events) == 2

    assert all(
        event.payment_id == first_payment_id
        for event in events
    )


def test_events_for_recovery():

    service = AuditService()

    first_recovery_id = uuid4()

    second_recovery_id = uuid4()

    service.record(
        AuditEventType.RECOVERY_PROPOSED,
        recovery_id=first_recovery_id,
    )

    service.record(
        AuditEventType.RECOVERY_SUCCEEDED,
        recovery_id=first_recovery_id,
    )

    service.record(
        AuditEventType.RECOVERY_PROPOSED,
        recovery_id=second_recovery_id,
    )

    events = service.events_for_recovery(
        first_recovery_id
    )

    assert len(events) == 2

    assert all(
        event.recovery_id == first_recovery_id
        for event in events
    )


def test_events_by_type():

    service = AuditService()

    service.record(
        AuditEventType.PAYMENT_DETECTED
    )

    service.record(
        AuditEventType.PAYMENT_DETECTED
    )

    service.record(
        AuditEventType.RECOVERY_PROPOSED
    )

    events = service.events_by_type(
        AuditEventType.PAYMENT_DETECTED
    )

    assert len(events) == 2

    assert all(
        event.event_type
        == AuditEventType.PAYMENT_DETECTED
        for event in events
    )


def test_metadata_is_recorded():

    service = AuditService()

    event = service.record(
        event_type=(
            AuditEventType.GUARDRAIL_BLOCKED
        ),
        metadata={
            "reason": "retry_limit_reached",
            "attempt_count": 3,
        },
    )

    assert event.metadata["reason"] == (
        "retry_limit_reached"
    )

    assert event.metadata["attempt_count"] == 3


def test_clear_removes_all_events():

    service = AuditService()

    service.record(
        AuditEventType.PAYMENT_DETECTED
    )

    service.record(
        AuditEventType.RECOVERY_PROPOSED
    )

    assert service.count() == 2

    service.clear()

    assert service.count() == 0