from uuid import UUID

from backend.app.domain.audit import AuditEvent
from simulator.audit.service import AuditService


class AuditPresenter:
    """
    Builds unified audit views from raw audit events.

    This layer is responsible for presentation and reporting,
    while AuditService remains responsible for event storage
    and querying.
    """

    def __init__(
        self,
        audit_service: AuditService,
    ) -> None:
        self.audit_service = audit_service

    def build_payment_timeline(
        self,
        payment_id: UUID,
    ) -> dict:
        """
        Build a chronological audit timeline
        for a specific payment.
        """

        events = self.audit_service.events_for_payment(
            payment_id
        )

        events = sorted(
            events,
            key=lambda event: event.created_at,
        )

        return {
            "payment_id": str(payment_id),
            "event_count": len(events),
            "timeline": [
                self._serialize_event(event)
                for event in events
            ],
        }

    def build_recovery_timeline(
        self,
        recovery_id: UUID,
    ) -> dict:
        """
        Build a chronological audit timeline
        for a recovery attempt.
        """

        events = self.audit_service.events_for_recovery(
            recovery_id
        )

        events = sorted(
            events,
            key=lambda event: event.created_at,
        )

        return {
            "recovery_id": str(recovery_id),
            "event_count": len(events),
            "timeline": [
                self._serialize_event(event)
                for event in events
            ],
        }

    def build_unified_timeline(
        self,
        payment_id: UUID,
        recovery_id: UUID | None = None,
    ) -> dict:
        """
        Build a unified payment and recovery timeline.
        """

        events = self.audit_service.events_for_payment(
            payment_id
        )

        if recovery_id is not None:
            recovery_events = (
                self.audit_service.events_for_recovery(
                    recovery_id
                )
            )

            event_ids = {
                event.event_id
                for event in events
            }

            for event in recovery_events:
                if event.event_id not in event_ids:
                    events.append(event)

        events = sorted(
            events,
            key=lambda event: event.created_at,
        )

        return {
            "payment_id": str(payment_id),
            "recovery_id": (
                str(recovery_id)
                if recovery_id is not None
                else None
            ),
            "event_count": len(events),
            "timeline": [
                self._serialize_event(event)
                for event in events
            ],
        }

    @staticmethod
    def _serialize_event(
        event: AuditEvent,
    ) -> dict:
        """
        Convert an AuditEvent into a
        JSON-friendly presentation format.
        """

        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type.value,
            "payment_id": (
                str(event.payment_id)
                if event.payment_id is not None
                else None
            ),
            "recovery_id": (
                str(event.recovery_id)
                if event.recovery_id is not None
                else None
            ),
            "timestamp": event.created_at.isoformat(),
            "metadata": event.metadata,
        }