from dataclasses import dataclass

from backend.app.domain.enums import (
    RecoveryStatus,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)


@dataclass(frozen=True)
class StrategyPerformance:
    """
    Performance metrics for a single
    recovery strategy.
    """

    strategy: str

    total_attempts: int

    successful_recoveries: int

    failed_recoveries: int

    success_rate: float

    revenue_recovered: float

    average_recovered_revenue: float


class RecoveryStrategyPerformance:
    """
    Calculates performance metrics for recovery
    strategies.

    This component is read-only and does not modify:

    - recovery orchestration
    - recovery execution
    - escalation
    - batch processing
    - recovery attempts

    It only analyzes completed batch results.
    """

    def analyze(
        self,
        *,
        batch_result: RecoveryBatchResult,
    ) -> list[StrategyPerformance]:
        """
        Analyze strategy performance and return
        strategies ranked by performance.
        """

        strategy_data: dict[
            str,
            dict[str, float | int],
        ] = {}

        for result in batch_result.results:

            orchestration = (
                result.orchestration
            )

            attempt = (
                orchestration.attempt
            )

            if attempt is None:
                continue

            strategy = self._get_strategy_value(
                attempt
            )

            if strategy not in strategy_data:

                strategy_data[
                    strategy
                ] = {
                    "total_attempts": 0,
                    "successful_recoveries": 0,
                    "failed_recoveries": 0,
                    "revenue_recovered": 0.0,
                }

            data = strategy_data[
                strategy
            ]

            data[
                "total_attempts"
            ] += 1

            if (
                attempt.status
                == RecoveryStatus.SUCCEEDED
            ):

                data[
                    "successful_recoveries"
                ] += 1

                data[
                    "revenue_recovered"
                ] += float(
                    attempt.actual_revenue
                    or 0.0
                )

            elif (
                attempt.status
                == RecoveryStatus.FAILED
            ):

                data[
                    "failed_recoveries"
                ] += 1

        performances = []

        for (
            strategy,
            data,
        ) in strategy_data.items():

            total_attempts = int(
                data[
                    "total_attempts"
                ]
            )

            successful_recoveries = int(
                data[
                    "successful_recoveries"
                ]
            )

            failed_recoveries = int(
                data[
                    "failed_recoveries"
                ]
            )

            revenue_recovered = float(
                data[
                    "revenue_recovered"
                ]
            )

            success_rate = (
                self._percentage(
                    numerator=(
                        successful_recoveries
                    ),
                    denominator=(
                        total_attempts
                    ),
                )
            )

            average_recovered_revenue = (
                self._average(
                    value=(
                        revenue_recovered
                    ),
                    count=(
                        successful_recoveries
                    ),
                )
            )

            performances.append(
                StrategyPerformance(
                    strategy=strategy,
                    total_attempts=(
                        total_attempts
                    ),
                    successful_recoveries=(
                        successful_recoveries
                    ),
                    failed_recoveries=(
                        failed_recoveries
                    ),
                    success_rate=(
                        success_rate
                    ),
                    revenue_recovered=(
                        revenue_recovered
                    ),
                    average_recovered_revenue=(
                        average_recovered_revenue
                    ),
                )
            )

        return sorted(
            performances,
            key=lambda performance: (
                performance.success_rate,
                performance.revenue_recovered,
            ),
            reverse=True,
        )

    def _get_strategy_value(
        self,
        attempt,
    ) -> str:
        """
        Normalize enum-based and string-based
        strategy values.
        """

        strategy = getattr(
            attempt,
            "strategy",
            None,
        )

        if strategy is None:
            return "unknown"

        value = getattr(
            strategy,
            "value",
            strategy,
        )

        return str(
            value
        )

    def _percentage(
        self,
        *,
        numerator: int,
        denominator: int,
    ) -> float:

        if denominator == 0:
            return 0.0

        return (
            numerator
            / denominator
        ) * 100

    def _average(
        self,
        *,
        value: float,
        count: int,
    ) -> float:

        if count == 0:
            return 0.0

        return (
            value
            / count
        )