from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)
from simulator.recovery.guardrails import (
    RecoveryGuardrails,
)


def create_payment(
    attempt_number: int = 1,
) -> Payment:

    return Payment(
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        attempt_number=attempt_number,
    )


def create_recovery(
    strategy: RecoveryStrategy = (
        RecoveryStrategy.RETRY_PAYMENT
    ),
) -> RecoveryAttempt:

    return RecoveryAttempt(
        payment_id=uuid4(),
        strategy=strategy,
        predicted_probability=0.8,
        predicted_revenue=Decimal("800"),
    )


def test_recovery_allowed():

    guardrails = RecoveryGuardrails()

    payment = create_payment(
        attempt_number=1,
    )

    attempt = create_recovery()

    decision = guardrails.evaluate(
        payment,
        attempt,
    )

    assert decision.allowed is True
    assert decision.action == "execute"


def test_max_retries_stops_recovery():

    guardrails = RecoveryGuardrails()

    payment = create_payment(
        attempt_number=3,
    )

    attempt = create_recovery()

    decision = guardrails.evaluate(
        payment,
        attempt,
    )

    assert decision.allowed is False
    assert decision.action == "stop"
    assert decision.should_escalate is True


def test_no_action_stops_recovery():

    guardrails = RecoveryGuardrails()

    payment = create_payment()

    attempt = create_recovery(
        RecoveryStrategy.NO_ACTION
    )

    decision = guardrails.evaluate(
        payment,
        attempt,
    )

    assert decision.allowed is False
    assert decision.action == "stop"


def test_escalation_strategy():

    guardrails = RecoveryGuardrails()

    payment = create_payment()

    attempt = create_recovery(
        RecoveryStrategy.ESCALATE
    )

    decision = guardrails.evaluate(
        payment,
        attempt,
    )

    assert decision.allowed is False
    assert decision.action == "escalate"
    assert decision.should_escalate is True


def test_terminal_recovery_is_blocked():

    guardrails = RecoveryGuardrails()

    payment = create_payment()

    attempt = create_recovery()

    attempt.status = (
        RecoveryStatus.SUCCEEDED
    )

    decision = guardrails.evaluate(
        payment,
        attempt,
    )

    assert decision.allowed is False
    assert decision.action == "stop"