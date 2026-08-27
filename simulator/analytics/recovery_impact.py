from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import RecoveryStatus, RecoveryStrategy
from backend.app.domain.models import RecoveryAttempt


@dataclass(frozen=True)
class RecoveryImpact:
    total_attempts: int
    successful_attempts: int
    failed_attempts: int

    predicted_revenue: Decimal
    actual_recovered_revenue: Decimal

    recovery_rate: float
    recovery_opportunity: Decimal

    attempts_by_strategy: dict[str, int]
    recovered_revenue_by_strategy: dict[str, Decimal]

    best_strategy: RecoveryStrategy | None


def calculate_recovery_impact(
    attempts: list[RecoveryAttempt],
) -> RecoveryImpact:

    total_attempts = len(attempts)

    successful_attempts = sum(
        attempt.status == RecoveryStatus.SUCCEEDED
        for attempt in attempts
    )

    failed_attempts = sum(
        attempt.status == RecoveryStatus.FAILED
        for attempt in attempts
    )

    predicted_revenue = sum(
        (
            attempt.predicted_revenue
            for attempt in attempts
        ),
        Decimal("0"),
    )

    actual_recovered_revenue = sum(
        (
            attempt.actual_revenue or Decimal("0")
            for attempt in attempts
            if attempt.status == RecoveryStatus.SUCCEEDED
        ),
        Decimal("0"),
    )

    recovery_rate = (
        successful_attempts / total_attempts
        if total_attempts
        else 0.0
    )

    recovery_opportunity = max(
        predicted_revenue - actual_recovered_revenue,
        Decimal("0"),
    )

    attempts_by_strategy: dict[str, int] = {}

    recovered_revenue_by_strategy: dict[str, Decimal] = {}

    for attempt in attempts:
        strategy = attempt.strategy.value

        attempts_by_strategy[strategy] = (
            attempts_by_strategy.get(strategy, 0) + 1
        )

        recovered_revenue_by_strategy[strategy] = (
            recovered_revenue_by_strategy.get(
                strategy,
                Decimal("0"),
            )
            + (
                attempt.actual_revenue
                if attempt.status == RecoveryStatus.SUCCEEDED
                and attempt.actual_revenue is not None
                else Decimal("0")
            )
        )

    best_strategy = None

    if recovered_revenue_by_strategy:
        best_strategy_value = max(
            recovered_revenue_by_strategy,
            key=recovered_revenue_by_strategy.get,
        )

        best_strategy = RecoveryStrategy(
            best_strategy_value
        )

    return RecoveryImpact(
        total_attempts=total_attempts,
        successful_attempts=successful_attempts,
        failed_attempts=failed_attempts,
        predicted_revenue=predicted_revenue,
        actual_recovered_revenue=actual_recovered_revenue,
        recovery_rate=recovery_rate,
        recovery_opportunity=recovery_opportunity,
        attempts_by_strategy=attempts_by_strategy,
        recovered_revenue_by_strategy=recovered_revenue_by_strategy,
        best_strategy=best_strategy,
    )