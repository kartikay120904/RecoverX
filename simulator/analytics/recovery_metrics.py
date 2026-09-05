from dataclasses import dataclass, field

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)


@dataclass
class StrategyPerformance:
    strategy: RecoveryStrategy
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0

    @property
    def success_rate(self) -> float:
        completed = (
            self.successful_attempts
            + self.failed_attempts
        )

        if completed == 0:
            return 0.0

        return round(
            self.successful_attempts
            / completed,
            4,
        )


@dataclass
class RecoveryPerformanceTracker:

    performances: dict[
        RecoveryStrategy,
        StrategyPerformance,
    ] = field(
        default_factory=dict
    )

    def record(
        self,
        attempt: RecoveryAttempt,
    ) -> None:

        if attempt.status not in {
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        }:
            return

        strategy = attempt.strategy

        if strategy not in self.performances:

            self.performances[
                strategy
            ] = StrategyPerformance(
                strategy=strategy
            )

        performance = (
            self.performances[
                strategy
            ]
        )

        performance.total_attempts += 1

        if (
            attempt.status
            == RecoveryStatus.SUCCEEDED
        ):

            performance.successful_attempts += 1

        elif (
            attempt.status
            == RecoveryStatus.FAILED
        ):

            performance.failed_attempts += 1

    def get_success_rate(
        self,
        strategy: RecoveryStrategy,
    ) -> float:

        performance = (
            self.performances.get(
                strategy
            )
        )

        if performance is None:
            return 0.0

        return (
            performance.success_rate
        )

    def get_all(
        self,
    ) -> list[StrategyPerformance]:

        return list(
            self.performances.values()
        )