from dataclasses import dataclass

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)


@dataclass(frozen=True)
class StrategyLearningSignal:
    """
    Historical learning signal for a
    recovery strategy.
    """

    strategy: RecoveryStrategy

    total_attempts: int

    successful_attempts: int

    historical_success_rate: float

    confidence_adjustment: float


@dataclass(frozen=True)
class AdaptiveProbability:
    """
    Result of applying historical learning
    to a baseline recovery probability.
    """

    strategy: RecoveryStrategy

    baseline_probability: float

    adjusted_probability: float

    confidence_adjustment: float

    historical_attempts: int

    historical_success_rate: float


def _clamp_probability(
    probability: float,
) -> float:
    """
    Keep probability within valid bounds.
    """

    return max(
        0.0,
        min(
            1.0,
            probability,
        ),
    )


def _historical_success_rate(
    attempts: list[RecoveryAttempt],
) -> float:
    """
    Calculate historical success rate.
    """

    if not attempts:
        return 0.0

    successful_attempts = sum(
        1
        for attempt in attempts
        if attempt.status
        == RecoveryStatus.SUCCEEDED
    )

    return round(
        successful_attempts
        / len(attempts),
        4,
    )


def build_learning_signals(
    attempts: list[RecoveryAttempt],
    baseline_probability: float = 0.50,
) -> list[StrategyLearningSignal]:
    """
    Build historical learning signals grouped
    by recovery strategy.

    confidence_adjustment represents the
    difference between observed historical
    performance and the supplied baseline.
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

    signals: list[
        StrategyLearningSignal
    ] = []

    for strategy, strategy_attempts in (
        grouped.items()
    ):

        successful_attempts = sum(
            1
            for attempt in strategy_attempts
            if attempt.status
            == RecoveryStatus.SUCCEEDED
        )

        success_rate = (
            _historical_success_rate(
                strategy_attempts
            )
        )

        adjustment = round(
            success_rate
            - baseline_probability,
            4,
        )

        signals.append(
            StrategyLearningSignal(
                strategy=strategy,
                total_attempts=len(
                    strategy_attempts
                ),
                successful_attempts=(
                    successful_attempts
                ),
                historical_success_rate=(
                    success_rate
                ),
                confidence_adjustment=(
                    adjustment
                ),
            )
        )

    return sorted(
        signals,
        key=lambda signal: (
            signal.strategy.value
        ),
    )


def apply_learning(
    *,
    strategy: RecoveryStrategy,
    baseline_probability: float,
    attempts: list[RecoveryAttempt],
    learning_weight: float = 0.25,
) -> AdaptiveProbability:
    """
    Apply historical recovery performance to
    a baseline probability.

    The learning weight controls how strongly
    historical outcomes influence the baseline.

    A weight of:
        0.0 -> no learning
        1.0 -> full historical adjustment
    """

    baseline = _clamp_probability(
        baseline_probability
    )

    weight = _clamp_probability(
        learning_weight
    )

    relevant_attempts = [
        attempt
        for attempt in attempts
        if attempt.strategy
        == strategy
    ]

    historical_attempts = len(
        relevant_attempts
    )

    if historical_attempts == 0:

        return AdaptiveProbability(
            strategy=strategy,
            baseline_probability=baseline,
            adjusted_probability=baseline,
            confidence_adjustment=0.0,
            historical_attempts=0,
            historical_success_rate=0.0,
        )

    historical_success_rate = (
        _historical_success_rate(
            relevant_attempts
        )
    )

    adjustment = (
        historical_success_rate
        - baseline
    )

    weighted_adjustment = (
        adjustment
        * weight
    )

    adjusted_probability = (
        _clamp_probability(
            baseline
            + weighted_adjustment
        )
    )

    return AdaptiveProbability(
        strategy=strategy,
        baseline_probability=baseline,
        adjusted_probability=round(
            adjusted_probability,
            4,
        ),
        confidence_adjustment=round(
            weighted_adjustment,
            4,
        ),
        historical_attempts=(
            historical_attempts
        ),
        historical_success_rate=(
            historical_success_rate
        ),
    )


def rank_adaptive_strategies(
    *,
    baseline_probabilities: dict[
        RecoveryStrategy,
        float,
    ],
    attempts: list[RecoveryAttempt],
    learning_weight: float = 0.25,
) -> list[AdaptiveProbability]:
    """
    Apply learning to multiple strategies and
    rank them by adjusted probability.
    """

    results = [
        apply_learning(
            strategy=strategy,
            baseline_probability=(
                baseline_probability
            ),
            attempts=attempts,
            learning_weight=(
                learning_weight
            ),
        )
        for (
            strategy,
            baseline_probability
        )
        in baseline_probabilities.items()
    ]

    return sorted(
        results,
        key=lambda result: (
            -result.adjusted_probability,
            result.strategy.value,
        ),
    )