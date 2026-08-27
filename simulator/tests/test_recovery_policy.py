from decimal import Decimal

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment, RecoveryAttempt
from simulator.recovery.policy import RecoveryPolicyEngine


def make_payment(
    amount: str = "1000",
    attempt_number: int = 1,
) -> Payment:
    return Payment(
        order_id="00000000-0000-0000-0000-000000000001",
        customer_id="00000000-0000-0000-0000-000000000002",
        amount=Decimal(amount),
        currency="INR",
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code="bank_timeout",
        attempt_number=attempt_number,
    )


def make_attempt(
    probability: float = 0.80,
    strategy: RecoveryStrategy = RecoveryStrategy.RETRY_PAYMENT,
) -> RecoveryAttempt:
    payment = make_payment()

    return RecoveryAttempt(
        payment_id=payment.payment_id,
        strategy=strategy,
        predicted_probability=probability,
        predicted_revenue=(
            payment.amount * Decimal(str(probability))
        ),
        status=RecoveryStatus.PROPOSED,
    )


def test_safe_recovery_is_allowed_without_approval():
    payment = make_payment()
    attempt = make_attempt()

    decision = RecoveryPolicyEngine().evaluate(
        attempt,
        payment,
    )

    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.risk_level == "low"


def test_low_confidence_requires_approval():
    payment = make_payment()
    attempt = make_attempt(probability=0.50)

    decision = RecoveryPolicyEngine().evaluate(
        attempt,
        payment,
    )

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.risk_level == "medium"


def test_high_value_payment_requires_approval():
    payment = make_payment(amount="60000")
    attempt = make_attempt(probability=0.90)

    decision = RecoveryPolicyEngine().evaluate(
        attempt,
        payment,
    )

    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.risk_level == "high"


def test_retry_limit_blocks_recovery():
    payment = make_payment(attempt_number=2)
    attempt = make_attempt(probability=0.90)

    decision = RecoveryPolicyEngine().evaluate(
        attempt,
        payment,
    )

    assert decision.allowed is False
    assert decision.requires_approval is False
    assert "Retry limit" in decision.reason


def test_no_action_is_blocked():
    payment = make_payment()

    attempt = make_attempt(
        strategy=RecoveryStrategy.NO_ACTION,
        probability=0.0,
    )

    decision = RecoveryPolicyEngine().evaluate(
        attempt,
        payment,
    )

    assert decision.allowed is False