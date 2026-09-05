from uuid import UUID

from backend.app.domain.audit import (
    AuditEvent,
    AuditEventType,
)


class AuditService:
    """
    In-memory audit infrastructure.

    Records significant recovery lifecycle events
    and provides query access for analytics,
    incident handling, escalation, and reporting.
    """

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        event_type: AuditEventType,
        payment_id: UUID | None = None,
        recovery_id: UUID | None = None,
        metadata: dict | None = None,
    ) -> AuditEvent:
        """
        Record a new audit event.
        """

        event = AuditEvent(
            event_type=event_type,
            payment_id=payment_id,
            recovery_id=recovery_id,
            metadata=metadata or {},
        )

        self._events.append(event)

        return event

    def all_events(self) -> list[AuditEvent]:
        """
        Return all recorded audit events.
        """

        return list(self._events)

    def events_for_payment(
        self,
        payment_id: UUID,
    ) -> list[AuditEvent]:
        """
        Return all events associated with
        a specific payment.
        """

        return [
            event
            for event in self._events
            if event.payment_id == payment_id
        ]

    def events_for_recovery(
        self,
        recovery_id: UUID,
    ) -> list[AuditEvent]:
        """
        Return all events associated with
        a specific recovery attempt.
        """

        return [
            event
            for event in self._events
            if event.recovery_id == recovery_id
        ]

    def events_by_type(
        self,
        event_type: AuditEventType,
    ) -> list[AuditEvent]:
        """
        Return all events matching an event type.
        """

        return [
            event
            for event in self._events
            if event.event_type == event_type
        ]

    def count(self) -> int:
        """
        Return the total number of audit events.
        """

        return len(self._events)

    def clear(self) -> None:
        """
        Clear all audit events.

        Useful for tests and simulation resets.
        """

        self._events.clear()