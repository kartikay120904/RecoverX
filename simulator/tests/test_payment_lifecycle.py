from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import PaymentMethod, PaymentStatus
from backend.app.domain.models import Payment
from simulator.event_stream import EventStream
from simulator.payment_lifecycle import PaymentLifecycle


def create_payment() -> Payment:
    return Payment(
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("5000"),
        method=PaymentMethod.UPI,
    )


def test_lifecycle_records_transition_event():
    stream = EventStream()
    lifecycle = PaymentLifecycle(stream)

    payment = create_payment()

    event = lifecycle.transition(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    assert payment.status == PaymentStatus.AUTHORIZED
    assert stream.count() == 1
    assert stream.all()[0] == event


def test_lifecycle_records_multiple_transitions():
    stream = EventStream()
    lifecycle = PaymentLifecycle(stream)

    payment = create_payment()

    lifecycle.transition(
        payment,
        PaymentStatus.AUTHORIZED,
        actor="payment_service",
    )

    lifecycle.transition(
        payment,
        PaymentStatus.CAPTURED,
        actor="payment_service",
    )

    events = stream.all()

    assert len(events) == 2

    assert events[0].payload["new_status"] == "authorized"
    assert events[1].payload["new_status"] == "captured"


def test_invalid_transition_does_not_create_event():
    stream = EventStream()
    lifecycle = PaymentLifecycle(stream)

    payment = create_payment()

    try:
        lifecycle.transition(
            payment,
            PaymentStatus.CAPTURED,
            actor="ai_agent",
        )
        assert False
    except Exception:
        pass

    assert stream.count() == 0