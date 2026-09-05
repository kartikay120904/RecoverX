from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import RecoveryEvent
from simulator.recovery.event_store import RecoveryEventStore


def make_event(
    payment_id=None,
    event_type="RECOVERY_PROPOSED",
    timestamp=None,
) -> RecoveryEvent:
    return RecoveryEvent(
        payment_id=payment_id or uuid4(),
        event_type=event_type,
        timestamp=timestamp
        or datetime.now(timezone.utc),
        strategy=RecoveryStrategy.RETRY_PAYMENT,
        status=RecoveryStatus.PROPOSED,
    )


def test_append_event():
    store = RecoveryEventStore()

    event = make_event()

    result = store.append(event)

    assert result == event
    assert store.count() == 1


def test_get_events_by_payment_id():
    store = RecoveryEventStore()

    payment_id = uuid4()

    first_event = make_event(
        payment_id=payment_id,
        event_type="RECOVERY_PROPOSED",
    )

    second_event = make_event(
        payment_id=payment_id,
        event_type="RECOVERY_APPROVED",
    )

    other_event = make_event()

    store.append(first_event)
    store.append(second_event)
    store.append(other_event)

    events = store.get_by_payment_id(
        payment_id
    )

    assert len(events) == 2
    assert events[0].payment_id == payment_id
    assert events[1].payment_id == payment_id


def test_events_are_returned_in_time_order():
    store = RecoveryEventStore()

    payment_id = uuid4()

    base_time = datetime.now(
        timezone.utc
    )

    later_event = make_event(
        payment_id=payment_id,
        event_type="RECOVERY_APPROVED",
        timestamp=base_time + timedelta(
            minutes=10
        ),
    )

    earlier_event = make_event(
        payment_id=payment_id,
        event_type="RECOVERY_PROPOSED",
        timestamp=base_time,
    )

    store.append(later_event)
    store.append(earlier_event)

    events = store.get_by_payment_id(
        payment_id
    )

    assert events[0].event_type == (
        "RECOVERY_PROPOSED"
    )

    assert events[1].event_type == (
        "RECOVERY_APPROVED"
    )


def test_get_all_events():
    store = RecoveryEventStore()

    first_event = make_event()
    second_event = make_event()

    store.append(first_event)
    store.append(second_event)

    events = store.get_all()

    assert len(events) == 2


def test_get_all_returns_copy():
    store = RecoveryEventStore()

    event = make_event()

    store.append(event)

    events = store.get_all()

    events.clear()

    assert store.count() == 1


def test_unknown_payment_returns_empty_list():
    store = RecoveryEventStore()

    events = store.get_by_payment_id(
        uuid4()
    )

    assert events == []


def test_clear_events():
    store = RecoveryEventStore()

    store.append(
        make_event()
    )

    store.append(
        make_event()
    )

    assert store.count() == 2

    store.clear()

    assert store.count() == 0