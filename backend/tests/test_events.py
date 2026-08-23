from decimal import Decimal
from uuid import uuid4

from app.domain.enums import PaymentMethod, PaymentStatus
from app.domain.models import Payment
from app.domain.state_machine import transition_payment


def test_transition_creates_unique_event():
    payment = Payment(
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000.00"),
        method=PaymentMethod.CARD,
    )

    event_1 = transition_payment(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    event_2 = transition_payment(
        payment,
        PaymentStatus.CAPTURED,
        actor="payment_service",
        correlation_id=event_1.correlation_id,
    )

    assert event_1.event_id != event_2.event_id
    assert event_1.correlation_id == event_2.correlation_id
    assert event_1.entity_id == payment.payment_id
    assert event_2.entity_id == payment.payment_id