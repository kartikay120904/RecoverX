from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
)

from simulator.recovery.diagnosis import (
    PaymentFailureDiagnoser,
)

from simulator.recovery.strategy import (
    RecoveryStrategyEngine,
)


def create_payment(
    failure_code: PaymentFailureCode,
    attempt_number: int = 1,
) -> Payment:

    return Payment(
        order_id=(
            "11111111-1111-1111-1111-111111111111"
        ),
        customer_id=(
            "22222222-2222-2222-2222-222222222222"
        ),
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=failure_code.value,
        attempt_number=attempt_number,
    )


def test_timeout_prefers_retry():

    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT
    )

    diagnosis = (
        PaymentFailureDiagnoser()
        .diagnose(payment)
    )

    decision = (
        RecoveryStrategyEngine()
        .decide(
            payment,
            diagnosis,
        )
    )

    assert (
        decision.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_insufficient_funds_prefers_reminder():

    payment = create_payment(
        PaymentFailureCode.INSUFFICIENT_FUNDS
    )

    diagnosis = (
        PaymentFailureDiagnoser()
        .diagnose(payment)
    )

    decision = (
        RecoveryStrategyEngine()
        .decide(
            payment,
            diagnosis,
        )
    )

    assert (
        decision.strategy
        == RecoveryStrategy.SEND_REMINDER
    )


def test_authentication_failure_prefers_link():

    payment = create_payment(
        PaymentFailureCode.AUTHENTICATION_FAILED
    )

    diagnosis = (
        PaymentFailureDiagnoser()
        .diagnose(payment)
    )

    decision = (
        RecoveryStrategyEngine()
        .decide(
            payment,
            diagnosis,
        )
    )

    assert (
        decision.strategy
        == RecoveryStrategy.RECOVERY_LINK
    )


def test_repeated_attempt_reduces_retry_score():

    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT,
        attempt_number=3,
    )

    diagnosis = (
        PaymentFailureDiagnoser()
        .diagnose(payment)
    )

    decision = (
        RecoveryStrategyEngine()
        .decide(
            payment,
            diagnosis,
        )
    )

    retry_score = next(
        item.score
        for item in decision.alternatives
        if (
            item.strategy
            == RecoveryStrategy.RETRY_PAYMENT
        )
    )

    assert retry_score < 0.90