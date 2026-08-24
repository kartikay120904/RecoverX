from uuid import UUID, uuid4

from backend.app.domain.enums import PaymentStatus
from backend.app.domain.events import DomainEvent
from backend.app.domain.models import Payment
from backend.app.domain.state_machine import transition_payment
from simulator.event_stream import EventStream


class PaymentLifecycle:
    def __init__(
        self,
        event_stream: EventStream,
    ) -> None:
        self.event_stream = event_stream

    def transition(
        self,
        payment: Payment,
        new_status: PaymentStatus,
        *,
        actor: str,
        correlation_id: UUID | None = None,
    ) -> DomainEvent:

        if correlation_id is None:
            correlation_id = uuid4()

        event = transition_payment(
            payment,
            new_status,
            actor=actor,
            correlation_id=correlation_id,
        )

        self.event_stream.append(event)

        return event