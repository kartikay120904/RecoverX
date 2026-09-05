from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)


@dataclass(frozen=True)
class RecoveryAnalytics:
    """
    Aggregated analytics for a collection
    of recovery attempts.
    """

    total_attempts: int

    succeeded_attempts: int

    failed_attempts: int

    pending_attempts: int

    success_rate: float

    total_predicted_revenue: Decimal

    total_actual_revenue: Decimal

    revenue_realization_rate: float


def _calculate_percentage(
    numerator: int | Decimal,
    denominator: int | Decimal,
) -> float:
    """
    Safely calculate a percentage-like ratio.

    Returns a value between 0 and 1.
    """

    if denominator == 0:
        return 0.0

    return round(
        float(numerator / denominator),
        4,
    )


def analyze_recoveries(
    attempts: list[RecoveryAttempt],
) -> RecoveryAnalytics:
    """
    Calculate aggregate recovery analytics.

    This function is read-only and does not
    modify the supplied recovery attempts.
    """

    total_attempts = len(
        attempts
    )

    succeeded_attempts = sum(
        1
        for attempt in attempts
        if attempt.status
        == RecoveryStatus.SUCCEEDED
    )

    failed_attempts = sum(
        1
        for attempt in attempts
        if attempt.status
        == RecoveryStatus.FAILED
    )

    pending_attempts = (
        total_attempts
        - succeeded_attempts
        - failed_attempts
    )

    success_rate = _calculate_percentage(
        succeeded_attempts,
        total_attempts,
    )

    total_predicted_revenue = sum(
        (
            attempt.predicted_revenue
            for attempt in attempts
        ),
        start=Decimal("0"),
    )

    total_actual_revenue = sum(
        (
            attempt.actual_revenue
            or Decimal("0")
            for attempt in attempts
        ),
        start=Decimal("0"),
    )

    revenue_realization_rate = (
        _calculate_percentage(
            total_actual_revenue,
            total_predicted_revenue,
        )
    )

    return RecoveryAnalytics(
        total_attempts=total_attempts,
        succeeded_attempts=succeeded_attempts,
        failed_attempts=failed_attempts,
        pending_attempts=pending_attempts,
        success_rate=success_rate,
        total_predicted_revenue=(
            total_predicted_revenue
        ),
        total_actual_revenue=(
            total_actual_revenue
        ),
        revenue_realization_rate=(
            revenue_realization_rate
        ),
    )


def recovery_success_rate_by_strategy(
    attempts: list[RecoveryAttempt],
) -> dict[RecoveryStrategy, float]:
    """
    Calculate recovery success rate grouped
    by recovery strategy.
    """

    strategies: dict[
        RecoveryStrategy,
        list[RecoveryAttempt],
    ] = {}

    for attempt in attempts:

        strategies.setdefault(
            attempt.strategy,
            [],
        ).append(
            attempt
        )

    result: dict[
        RecoveryStrategy,
        float,
    ] = {}

    for strategy, strategy_attempts in (
        strategies.items()
    ):

        succeeded = sum(
            1
            for attempt in strategy_attempts
            if attempt.status
            == RecoveryStatus.SUCCEEDED
        )

        result[strategy] = (
            _calculate_percentage(
                succeeded,
                len(strategy_attempts),
            )
        )

    return result


def revenue_by_strategy(
    attempts: list[RecoveryAttempt],
) -> dict[
    RecoveryStrategy,
    Decimal,
]:
    """
    Calculate realized revenue grouped
    by recovery strategy.
    """

    result: dict[
        RecoveryStrategy,
        Decimal,
    ] = {}

    for attempt in attempts:

        current_revenue = (
            result.get(
                attempt.strategy,
                Decimal("0"),
            )
        )

        actual_revenue = (
            attempt.actual_revenue
            or Decimal("0")
        )

        result[
            attempt.strategy
        ] = (
            current_revenue
            + actual_revenue
        )

    return result