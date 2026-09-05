from uuid import UUID

from backend.app.domain.models import (
    RecoveryEvent,
)


class RecoveryEventStore:
    """
    In-memory append-only event store.

    The store maintains an immutable-style
    audit trail for recovery lifecycle events.
    """

    def __init__(
        self,
    ) -> None:
        self._events: list[
            RecoveryEvent
        ] = []

    def append(
        self,
        event: RecoveryEvent,
    ) -> RecoveryEvent:
        """
        Append an event to the recovery timeline.

        A deep copy is stored so external callers
        cannot mutate the persisted event.
        """

        stored_event = event.model_copy(
            deep=True,
        )

        self._events.append(
            stored_event
        )

        return stored_event.model_copy(
            deep=True,
        )

    def get_by_payment_id(
        self,
        payment_id: UUID,
    ) -> list[RecoveryEvent]:
        """
        Return events for a payment in
        chronological order.

        Copies are returned to protect
        internal event history.
        """

        events = [
            event
            for event in self._events
            if event.payment_id == payment_id
        ]

        events = sorted(
            events,
            key=lambda event: event.timestamp,
        )

        return [
            event.model_copy(
                deep=True,
            )
            for event in events
        ]

    def get_all(
        self,
    ) -> list[RecoveryEvent]:
        """
        Return copies of all events.
        """

        return [
            event.model_copy(
                deep=True,
            )
            for event in self._events
        ]

    def count(
        self,
    ) -> int:
        """
        Return the total number of events.
        """

        return len(
            self._events
        )

    def clear(
        self,
    ) -> None:
        """
        Clear all events.

        Primarily useful for tests and
        simulation resets.
        """

        self._events.clear()