from collections import defaultdict

from backend.app.domain.events import DomainEvent


class EventStore:
    """
    In-memory append-only event store.

    Stores domain events and allows events to be
    queried by entity ID or event type.

    This component is intentionally independent
    from the recovery workflow so existing domain
    behavior remains unchanged.
    """

    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

        self._events_by_entity: dict[
            object,
            list[DomainEvent],
        ] = defaultdict(list)

        self._events_by_type: dict[
            str,
            list[DomainEvent],
        ] = defaultdict(list)

    def append(
        self,
        event: DomainEvent,
    ) -> None:
        """
        Append a domain event to the store.
        """

        self._events.append(event)

        self._events_by_entity[
            event.entity_id
        ].append(event)

        self._events_by_type[
            event.event_type
        ].append(event)

    def all_events(
        self,
    ) -> tuple[DomainEvent, ...]:
        """
        Return all events in insertion order.
        """

        return tuple(
            self._events
        )

    def events_for_entity(
        self,
        entity_id: object,
    ) -> tuple[DomainEvent, ...]:
        """
        Return events belonging to an entity.
        """

        return tuple(
            self._events_by_entity.get(
                entity_id,
                [],
            )
        )

    def events_of_type(
        self,
        event_type: str,
    ) -> tuple[DomainEvent, ...]:
        """
        Return all events of a specific type.
        """

        return tuple(
            self._events_by_type.get(
                event_type,
                [],
            )
        )

    def count(
        self,
    ) -> int:
        """
        Return the total number of stored events.
        """

        return len(
            self._events
        )

    def clear(
        self,
    ) -> None:
        """
        Remove all stored events.
        """

        self._events.clear()

        self._events_by_entity.clear()

        self._events_by_type.clear()