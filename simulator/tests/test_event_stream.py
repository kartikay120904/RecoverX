from uuid import uuid4

from backend.app.domain.events import DomainEvent
from simulator.event_stream import EventStream


def create_event() -> DomainEvent:
    return DomainEvent(
        event_type="test.event",
        entity_id=uuid4(),
        correlation_id=uuid4(),
        actor="test",
        payload={"value": 123},
    )


def test_append_event():
    stream = EventStream()
    event = create_event()

    stream.append(event)

    assert stream.count() == 1
    assert stream.all()[0] == event


def test_events_are_returned_in_order():
    stream = EventStream()

    event_1 = create_event()
    event_2 = create_event()

    stream.append(event_1)
    stream.append(event_2)

    events = stream.all()

    assert events == [event_1, event_2]


def test_all_returns_copy():
    stream = EventStream()
    event = create_event()

    stream.append(event)

    events = stream.all()
    events.clear()

    assert stream.count() == 1