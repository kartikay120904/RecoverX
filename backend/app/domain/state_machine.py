from uuid import UUID, uuid4

from .enums import PaymentStatus
from .events import DomainEvent
from .models import Payment


class InvalidPaymentTransition(Exception):
    """Raised when a payment attempts an invalid state transition."""


ALLOWED_TRANSITIONS: dict[PaymentStatus, set[PaymentStatus]] = {
    PaymentStatus.CREATED: {
        PaymentStatus.AUTHORIZED,
        PaymentStatus.FAILED,
    },
    PaymentStatus.AUTHORIZED: {
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED,
    },
    PaymentStatus.CAPTURED: {
        PaymentStatus.REFUNDED,
    },
    PaymentStatus.FAILED: {
        PaymentStatus.RETRY_ELIGIBLE,
    },
    PaymentStatus.RETRY_ELIGIBLE: {
        PaymentStatus.RETRYING,
    },
    PaymentStatus.RETRYING: {
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED,
    },
    PaymentStatus.REFUNDED: set(),
}


def transition_payment(
    payment: Payment,
    new_status: PaymentStatus,
    *,
    actor: str,
    correlation_id: UUID | None = None,
) -> DomainEvent:
    allowed = ALLOWED_TRANSITIONS[payment.status]

    if new_status not in allowed:
        raise InvalidPaymentTransition(
            f"Invalid payment transition: "
            f"{payment.status.value} -> {new_status.value}"
        )

    previous_status = payment.status

    payment.status = new_status

    if correlation_id is None:
        correlation_id = uuid4()

    return DomainEvent(
        event_type="payment.status_changed",
        entity_id=payment.payment_id,
        correlation_id=correlation_id,
        actor=actor,
        payload={
            "previous_status": previous_status.value,
            "new_status": new_status.value,
            "attempt_number": payment.attempt_number,
        },
    )