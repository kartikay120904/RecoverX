from backend.app.domain.enums import (
    RecoveryStatus,
)

from simulator.analytics.strategy_performance import (
    RecoveryStrategyPerformance,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)

from simulator.batch.recovery_metrics import (
    RecoveryMetrics,
)


class StubAttempt:

    def __init__(
        self,
        *,
        strategy,
        status,
        actual_revenue=0.0,
    ) -> None:

        self.strategy = strategy

        self.status = status

        self.actual_revenue = (
            actual_revenue
        )


class StubResult:

    def __init__(
        self,
        *,
        attempt=None,
    ) -> None:

        class Orchestration:
            pass

        self.orchestration = (
            Orchestration()
        )

        self.orchestration.attempt = (
            attempt
        )


def create_batch_result(
    results,
) -> RecoveryBatchResult:

    return RecoveryBatchResult(
        results=results,
        metrics=RecoveryMetrics(),
    )


def test_empty_strategy_performance():

    result = create_batch_result(
        results=[],
    )

    performances = (
        RecoveryStrategyPerformance().analyze(
            batch_result=result,
        )
    )

    assert performances == []


def test_strategy_metrics():

    retry_success = StubAttempt(
        strategy="retry",
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=1000.0,
    )

    retry_failure = StubAttempt(
        strategy="retry",
        status=RecoveryStatus.FAILED,
    )

    alternate_success = StubAttempt(
        strategy="alternate_method",
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=500.0,
    )

    result = create_batch_result(
        results=[
            StubResult(
                attempt=retry_success,
            ),
            StubResult(
                attempt=retry_failure,
            ),
            StubResult(
                attempt=alternate_success,
            ),
        ],
    )

    performances = (
        RecoveryStrategyPerformance().analyze(
            batch_result=result,
        )
    )

    performance_by_strategy = {
        performance.strategy: performance
        for performance in performances
    }

    retry = (
        performance_by_strategy[
            "retry"
        ]
    )

    assert retry.total_attempts == 2

    assert (
        retry.successful_recoveries
        == 1
    )

    assert (
        retry.failed_recoveries
        == 1
    )

    assert (
        retry.success_rate
        == 50.0
    )

    assert (
        retry.revenue_recovered
        == 1000.0
    )

    assert (
        retry.average_recovered_revenue
        == 1000.0
    )

    alternate = (
        performance_by_strategy[
            "alternate_method"
        ]
    )

    assert (
        alternate.total_attempts
        == 1
    )

    assert (
        alternate.success_rate
        == 100.0
    )

    assert (
        alternate.revenue_recovered
        == 500.0
    )


def test_strategy_ranking():

    low_performance = StubAttempt(
        strategy="retry",
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=100.0,
    )

    low_failure = StubAttempt(
        strategy="retry",
        status=RecoveryStatus.FAILED,
    )

    high_performance = StubAttempt(
        strategy="alternate_method",
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=500.0,
    )

    result = create_batch_result(
        results=[
            StubResult(
                attempt=low_performance,
            ),
            StubResult(
                attempt=low_failure,
            ),
            StubResult(
                attempt=high_performance,
            ),
        ],
    )

    performances = (
        RecoveryStrategyPerformance().analyze(
            batch_result=result,
        )
    )

    assert (
        performances[0].strategy
        == "alternate_method"
    )

    assert (
        performances[1].strategy
        == "retry"
    )


def test_unknown_strategy():

    attempt = StubAttempt(
        strategy=None,
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=100.0,
    )

    result = create_batch_result(
        results=[
            StubResult(
                attempt=attempt,
            ),
        ],
    )

    performances = (
        RecoveryStrategyPerformance().analyze(
            batch_result=result,
        )
    )

    assert len(
        performances
    ) == 1

    assert (
        performances[0].strategy
        == "unknown"
    )