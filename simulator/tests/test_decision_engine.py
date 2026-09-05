from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment

from backend.app.services.decision_engine import (
    build_recovery_attempt_data,
    rank_strategies,
    select_best_strategy,
)


def create_payment(
    failure_code,
    amount="10000",
):
    return Payment(
        amount=Decimal(amount),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=failure_code,
    )


def test_timeout_prefers_retry():
    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    decision = select_best_strategy(
        payment,
        "high",
    )

    assert (
        decision.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )

    assert (
        decision.predicted_probability
        > 0.5
    )


def test_insufficient_funds_prefers_reminder():
    payment = create_payment(
        PaymentFailureCode.INSUFFICIENT_FUNDS.value
    )

    decision = select_best_strategy(
        payment
    )

    assert (
        decision.strategy
        == RecoveryStrategy.SEND_REMINDER
    )


def test_authentication_prefers_recovery_link():
    payment = create_payment(
        PaymentFailureCode.AUTHENTICATION_FAILED.value
    )

    decision = select_best_strategy(
        payment
    )

    assert (
        decision.strategy
        == RecoveryStrategy.RECOVERY_LINK
    )


def test_predicted_revenue():
    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT.value,
        amount="10000",
    )

    decision = select_best_strategy(
        payment
    )

    assert (
        decision.predicted_revenue
        == Decimal("8500.00")
    )


def test_ranked_strategies_are_deterministic():
    payment = create_payment(
        PaymentFailureCode.PAYMENT_DECLINED.value
    )

    first = rank_strategies(
        payment
    )

    second = rank_strategies(
        payment
    )

    assert first == second


def test_build_recovery_attempt_data():
    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    data = build_recovery_attempt_data(
        payment,
        "high",
    )

    assert (
        data["strategy"]
        == RecoveryStrategy.RETRY_PAYMENT
    )

    assert (
        data["predicted_probability"]
        >= 0
    )

    assert (
        data["predicted_probability"]
        <= 1
    )

    assert (
        data["predicted_revenue"]
        > Decimal("0")
    )

    assert (
        data["decision_score"]
        >= 0
    )

    assert (
        data["decision_score"]
        <= 1
    )