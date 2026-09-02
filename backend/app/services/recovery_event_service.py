from collections import defaultdict
from typing import Iterable
from uuid import UUID

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import RecoveryEvent


class RecoveryEventService:
    """
    In-memory immutable event store for the recovery lifecycle.

    The service records recovery events for each payment and
    provides the payment's recovery audit timeline.

    This implementation is intentionally storage-agnostic so it
    can later be replaced by PostgreSQL, Redis Streams, Kafka,
    or another persistent event backend.
    """

    def __init__(self) -> None:
        self._events: dict[
            UUID,
            list[RecoveryEvent],
        ] = defaultdict(list)

    def record_event(
        self,
        *,
        payment_id: UUID,
        event_type: str,
        status: RecoveryStatus | None = None,
        strategy: RecoveryStrategy | None = None,
        details: str | None = None,
        metadata: dict[
            str,
            str | int | float | bool | None,
        ]
        | None = None,
    ) -> RecoveryEvent:
        """
        Create and store an immutable recovery event.
        """

        event = RecoveryEvent(
            payment_id=payment_id,
            event_type=event_type,
            status=status,
            strategy=strategy,
            details=details,
            metadata=metadata or {},
        )

        self._events[payment_id].append(event)

        return event

    def get_events(
        self,
        payment_id: UUID,
    ) -> list[RecoveryEvent]:
        """
        Return the complete recovery timeline for a payment.
        """

        return list(
            self._events.get(
                payment_id,
                [],
            )
        )

    def get_latest_event(
        self,
        payment_id: UUID,
    ) -> RecoveryEvent | None:
        """
        Return the latest recovery event for a payment.
        """

        events = self._events.get(
            payment_id,
            [],
        )

        if not events:
            return None

        return events[-1]

    def count_events(
        self,
        payment_id: UUID,
    ) -> int:
        """
        Return the number of recovery events recorded for a payment.
        """

        return len(
            self._events.get(
                payment_id,
                [],
            )
        )

    def iter_events(
        self,
        payment_id: UUID,
    ) -> Iterable[RecoveryEvent]:
        """
        Iterate through events in chronological order.
        """

        yield from self._events.get(
            payment_id,
            [],
        )

    def clear_events(
        self,
        payment_id: UUID,
    ) -> None:
        """
        Clear events for a payment.

        Intended primarily for tests and simulator resets.
        """

        self._events.pop(
            payment_id,
            None,
        )


recovery_event_service = RecoveryEventService()