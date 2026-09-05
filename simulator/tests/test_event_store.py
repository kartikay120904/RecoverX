from uuid import uuid4

from backend.app.domain.events import (
    DomainEvent,
)

from simulator.events.store import (
    EventStore,
)


def make_event(
    *,
    entity_id=None,
    event_type: str = (
        "recovery.status_changed"
    ),
) -> DomainEvent:

    return DomainEvent(
        event_type=event_type,
        entity_id=(
            entity_id
            if entity_id is not None
            else uuid4()
        ),
        actor="test",
    )


def test_event_store_appends_event():

    store = EventStore()

    event = make_event()

    store.append(
        event
    )

    assert store.count() == 1

    assert store.all_events() == (
        event,
    )


def test_event_store_preserves_order():

    store = EventStore()

    first = make_event()

    second = make_event()

    store.append(first)

    store.append(second)

    assert store.all_events() == (
        first,
        second,
    )


def test_event_store_filters_by_entity():

    store = EventStore()

    entity_id = uuid4()

    matching_event = make_event(
        entity_id=entity_id,
    )

    other_event = make_event()

    store.append(
        matching_event
    )

    store.append(
        other_event
    )

    events = (
        store.events_for_entity(
            entity_id
        )
    )

    assert events == (
        matching_event,
    )


def test_event_store_filters_by_type():

    store = EventStore()

    recovery_event = make_event(
        event_type=(
            "recovery.status_changed"
        )
    )

    payment_event = make_event(
        event_type=(
            "payment.status_changed"
        )
    )

    store.append(
        recovery_event
    )

    store.append(
        payment_event
    )

    events = (
        store.events_of_type(
            "recovery.status_changed"
        )
    )

    assert events == (
        recovery_event,
    )


def test_event_store_clear():

    store = EventStore()

    store.append(
        make_event()
    )

    assert store.count() == 1

    store.clear()

    assert store.count() == 0

    assert store.all_events() == ()