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
class StrategyInsight:
    """
    Historical performance insight for a
    single recovery strategy.
    """

    strategy: RecoveryStrategy

    total_attempts: int

    successful_attempts: int

    failed_attempts: int

    success_rate: float

    total_revenue: Decimal

    average_revenue: Decimal


@dataclass(frozen=True)
class RecoveryInsights:
    """
    Aggregated historical insights across
    recovery strategies.
    """

    strategies: list[StrategyInsight]

    best_strategy: RecoveryStrategy | None

    worst_strategy: RecoveryStrategy | None

    underperforming_strategies: list[
        RecoveryStrategy
    ]


def _success_rate(
    successful_attempts: int,
    total_attempts: int,
) -> float:
    """
    Calculate a safe success rate.
    """

    if total_attempts == 0:
        return 0.0

    return round(
        successful_attempts
        / total_attempts,
        4,
    )


def _average_revenue(
    total_revenue: Decimal,
    total_attempts: int,
) -> Decimal:
    """
    Calculate average realized revenue.
    """

    if total_attempts == 0:
        return Decimal("0")

    return (
        total_revenue
        / Decimal(str(total_attempts))
    ).quantize(
        Decimal("0.01")
    )


def build_strategy_insights(
    attempts: list[RecoveryAttempt],
) -> list[StrategyInsight]:
    """
    Build historical performance metrics
    for each recovery strategy.

    This function does not modify attempts.
    """

    grouped: dict[
        RecoveryStrategy,
        list[RecoveryAttempt],
    ] = {}

    for attempt in attempts:

        grouped.setdefault(
            attempt.strategy,
            [],
        ).append(
            attempt
        )

    insights: list[
        StrategyInsight
    ] = []

    for strategy, strategy_attempts in (
        grouped.items()
    ):

        total_attempts = len(
            strategy_attempts
        )

        successful_attempts = sum(
            1
            for attempt in strategy_attempts
            if attempt.status
            == RecoveryStatus.SUCCEEDED
        )

        failed_attempts = sum(
            1
            for attempt in strategy_attempts
            if attempt.status
            == RecoveryStatus.FAILED
        )

        total_revenue = sum(
            (
                attempt.actual_revenue
                or Decimal("0")
                for attempt in strategy_attempts
            ),
            start=Decimal("0"),
        )

        insights.append(
            StrategyInsight(
                strategy=strategy,
                total_attempts=total_attempts,
                successful_attempts=(
                    successful_attempts
                ),
                failed_attempts=(
                    failed_attempts
                ),
                success_rate=_success_rate(
                    successful_attempts,
                    total_attempts,
                ),
                total_revenue=(
                    total_revenue
                ),
                average_revenue=(
                    _average_revenue(
                        total_revenue,
                        total_attempts,
                    )
                ),
            )
        )

    return sorted(
        insights,
        key=lambda insight: (
            -insight.success_rate,
            -float(
                insight.average_revenue
            ),
            insight.strategy.value,
        ),
    )


def identify_best_strategy(
    insights: list[StrategyInsight],
) -> RecoveryStrategy | None:
    """
    Return the best performing strategy.
    """

    if not insights:
        return None

    best = max(
        insights,
        key=lambda insight: (
            insight.success_rate,
            insight.average_revenue,
            insight.strategy.value,
        ),
    )

    return best.strategy


def identify_worst_strategy(
    insights: list[StrategyInsight],
) -> RecoveryStrategy | None:
    """
    Return the worst performing strategy.
    """

    if not insights:
        return None

    worst = min(
        insights,
        key=lambda insight: (
            insight.success_rate,
            insight.average_revenue,
            insight.strategy.value,
        ),
    )

    return worst.strategy


def identify_underperforming_strategies(
    insights: list[StrategyInsight],
    minimum_success_rate: float = 0.50,
    minimum_attempts: int = 2,
) -> list[RecoveryStrategy]:
    """
    Identify strategies with enough historical
    observations that perform below the required
    success rate.
    """

    result: list[
        RecoveryStrategy
    ] = []

    for insight in insights:

        if (
            insight.total_attempts
            < minimum_attempts
        ):
            continue

        if (
            insight.success_rate
            < minimum_success_rate
        ):
            result.append(
                insight.strategy
            )

    return sorted(
        result,
        key=lambda strategy: (
            strategy.value
        ),
    )


def generate_recovery_insights(
    attempts: list[RecoveryAttempt],
    minimum_success_rate: float = 0.50,
    minimum_attempts: int = 2,
) -> RecoveryInsights:
    """
    Generate complete historical recovery
    strategy intelligence.
    """

    strategies = (
        build_strategy_insights(
            attempts
        )
    )

    return RecoveryInsights(
        strategies=strategies,
        best_strategy=(
            identify_best_strategy(
                strategies
            )
        ),
        worst_strategy=(
            identify_worst_strategy(
                strategies
            )
        ),
        underperforming_strategies=(
            identify_underperforming_strategies(
                strategies,
                minimum_success_rate,
                minimum_attempts,
            )
        ),
    )