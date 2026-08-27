from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import RecoveryAttempt
from simulator.analytics.recovery_impact import (
    calculate_recovery_impact,
)


def create_attempt(
    strategy: RecoveryStrategy,
    status: RecoveryStatus,
    predicted_revenue: str,
    actual_revenue: str | None,
) -> RecoveryAttempt:
    return RecoveryAttempt(
        payment_id=uuid4(),
        strategy=strategy,
        predicted_probability=0.5,
        predicted_revenue=Decimal(predicted_revenue),
        actual_revenue=(
            Decimal(actual_revenue)
            if actual_revenue is not None
            else None
        ),
        status=status,
    )


def test_recovery_impact_calculates_totals():
    attempts = [
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.SUCCEEDED,
            "700",
            "1000",
        ),
        create_attempt(
            RecoveryStrategy.SEND_REMINDER,
            RecoveryStatus.FAILED,
            "300",
            "0",
        ),
    ]

    impact = calculate_recovery_impact(attempts)

    assert impact.total_attempts == 2
    assert impact.successful_attempts == 1
    assert impact.failed_attempts == 1

    assert impact.predicted_revenue == Decimal("1000")
    assert impact.actual_recovered_revenue == Decimal("1000")

    assert impact.recovery_rate == 0.5


def test_recovery_opportunity_never_goes_negative():
    attempts = [
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.SUCCEEDED,
            "500",
            "1000",
        ),
    ]

    impact = calculate_recovery_impact(attempts)

    assert impact.recovery_opportunity == Decimal("0")


def test_strategy_breakdown():
    attempts = [
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.SUCCEEDED,
            "700",
            "1000",
        ),
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.FAILED,
            "700",
            "0",
        ),
        create_attempt(
            RecoveryStrategy.SEND_REMINDER,
            RecoveryStatus.SUCCEEDED,
            "300",
            "500",
        ),
    ]

    impact = calculate_recovery_impact(attempts)

    assert impact.attempts_by_strategy == {
        "retry_payment": 2,
        "send_reminder": 1,
    }

    assert impact.recovered_revenue_by_strategy == {
        "retry_payment": Decimal("1000"),
        "send_reminder": Decimal("500"),
    }

    assert (
        impact.best_strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_empty_recovery_attempts():
    impact = calculate_recovery_impact([])

    assert impact.total_attempts == 0
    assert impact.successful_attempts == 0
    assert impact.failed_attempts == 0

    assert impact.predicted_revenue == Decimal("0")
    assert impact.actual_recovered_revenue == Decimal("0")
    assert impact.recovery_rate == 0.0
    assert impact.recovery_opportunity == Decimal("0")

    assert impact.attempts_by_strategy == {}
    assert impact.recovered_revenue_by_strategy == {}
    assert impact.best_strategy is None