from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from backend.app.services.recovery_learning import (
    apply_learning,
    build_learning_signals,
    rank_adaptive_strategies,
)


def make_attempt(
    *,
    strategy: RecoveryStrategy,
    status: RecoveryStatus,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        strategy=strategy,
        predicted_probability=0.50,
        predicted_revenue=Decimal("100"),
        actual_revenue=(
            Decimal("100")
            if status
            == RecoveryStatus.SUCCEEDED
            else Decimal("0")
        ),
        status=status,
    )


def test_empty_learning_signals():

    signals = (
        build_learning_signals(
            []
        )
    )

    assert signals == []


def test_build_learning_signals():

    attempts = [
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.FAILED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.RECOVERY_LINK
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
    ]

    signals = (
        build_learning_signals(
            attempts
        )
    )

    retry_signal = next(
        signal
        for signal in signals
        if signal.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )

    assert (
        retry_signal.total_attempts
        == 2
    )

    assert (
        retry_signal.successful_attempts
        == 1
    )

    assert (
        retry_signal.historical_success_rate
        == 0.5
    )

    assert (
        retry_signal.confidence_adjustment
        == 0.0
    )


def test_apply_learning_without_history():

    result = apply_learning(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        baseline_probability=0.70,
        attempts=[],
    )

    assert (
        result.adjusted_probability
        == 0.70
    )

    assert (
        result.confidence_adjustment
        == 0.0
    )

    assert (
        result.historical_attempts
        == 0
    )


def test_learning_improves_probability():

    attempts = [
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
    ]

    result = apply_learning(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        baseline_probability=0.50,
        attempts=attempts,
        learning_weight=0.50,
    )

    assert (
        result.historical_success_rate
        == 1.0
    )

    assert (
        result.adjusted_probability
        == 0.75
    )

    assert (
        result.confidence_adjustment
        == 0.25
    )


def test_learning_reduces_probability():

    attempts = [
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.FAILED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.FAILED
            ),
        ),
    ]

    result = apply_learning(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        baseline_probability=0.80,
        attempts=attempts,
        learning_weight=0.50,
    )

    assert (
        result.historical_success_rate
        == 0.0
    )

    assert (
        result.adjusted_probability
        == 0.40
    )

    assert (
        result.confidence_adjustment
        == -0.40
    )


def test_learning_only_uses_matching_strategy():

    attempts = [
        make_attempt(
            strategy=(
                RecoveryStrategy.RECOVERY_LINK
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
    ]

    result = apply_learning(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        baseline_probability=0.60,
        attempts=attempts,
    )

    assert (
        result.adjusted_probability
        == 0.60
    )

    assert (
        result.historical_attempts
        == 0
    )


def test_rank_adaptive_strategies():

    attempts = [
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.RETRY_PAYMENT
            ),
            status=(
                RecoveryStatus.SUCCEEDED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.SEND_REMINDER
            ),
            status=(
                RecoveryStatus.FAILED
            ),
        ),
        make_attempt(
            strategy=(
                RecoveryStrategy.SEND_REMINDER
            ),
            status=(
                RecoveryStatus.FAILED
            ),
        ),
    ]

    results = (
        rank_adaptive_strategies(
            baseline_probabilities={
                RecoveryStrategy.RETRY_PAYMENT: (
                    0.50
                ),
                RecoveryStrategy.SEND_REMINDER: (
                    0.50
                ),
            },
            attempts=attempts,
            learning_weight=0.50,
        )
    )

    assert (
        results[0].strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )

    assert (
        results[1].strategy
        == RecoveryStrategy.SEND_REMINDER
    )

    assert (
        results[0].adjusted_probability
        > results[1].adjusted_probability
    )


def test_probability_is_clamped():

    result = apply_learning(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        baseline_probability=2.0,
        attempts=[],
    )

    assert (
        result.adjusted_probability
        == 1.0
    )