from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import RecoveryAttempt


class RecoveryAnalytics:
    """
    Calculates analytics for recovery attempts.

    This module is read-only: it does not modify recovery attempts.
    """

    def total_attempts(
        self,
        attempts: list[RecoveryAttempt],
    ) -> int:

        return len(attempts)

    def successful_attempts(
        self,
        attempts: list[RecoveryAttempt],
    ) -> int:

        return sum(
            1
            for attempt in attempts
            if attempt.status
            == RecoveryStatus.SUCCEEDED
        )

    def failed_attempts(
        self,
        attempts: list[RecoveryAttempt],
    ) -> int:

        return sum(
            1
            for attempt in attempts
            if attempt.status
            == RecoveryStatus.FAILED
        )

    def predicted_revenue(
        self,
        attempts: list[RecoveryAttempt],
    ) -> Decimal:

        return sum(
            (
                attempt.predicted_revenue
                for attempt in attempts
            ),
            Decimal("0"),
        )

    def actual_recovered_revenue(
        self,
        attempts: list[RecoveryAttempt],
    ) -> Decimal:

        return sum(
            (
                attempt.actual_revenue
                for attempt in attempts
                if attempt.actual_revenue is not None
            ),
            Decimal("0"),
        )

    def recovery_rate(
        self,
        attempts: list[RecoveryAttempt],
    ) -> float:

        total = self.total_attempts(attempts)

        if total == 0:
            return 0.0

        successful = self.successful_attempts(
            attempts
        )

        return round(
            successful / total,
            4,
        )

    def strategy_performance(
        self,
        attempts: list[RecoveryAttempt],
    ) -> dict[
        RecoveryStrategy,
        dict[str, int | Decimal | float],
    ]:

        performance = {}

        for strategy in RecoveryStrategy:

            strategy_attempts = [
                attempt
                for attempt in attempts
                if attempt.strategy == strategy
            ]

            total = len(strategy_attempts)

            successful = sum(
                1
                for attempt in strategy_attempts
                if attempt.status
                == RecoveryStatus.SUCCEEDED
            )

            predicted_revenue = sum(
                (
                    attempt.predicted_revenue
                    for attempt in strategy_attempts
                ),
                Decimal("0"),
            )

            actual_revenue = sum(
                (
                    attempt.actual_revenue
                    for attempt in strategy_attempts
                    if attempt.actual_revenue
                    is not None
                ),
                Decimal("0"),
            )

            success_rate = (
                round(successful / total, 4)
                if total > 0
                else 0.0
            )

            performance[strategy] = {
                "total_attempts": total,
                "successful_attempts": successful,
                "predicted_revenue": predicted_revenue,
                "actual_revenue": actual_revenue,
                "success_rate": success_rate,
            }

        return performance

    def summary(
        self,
        attempts: list[RecoveryAttempt],
    ) -> dict[str, int | Decimal | float]:

        return {
            "total_attempts": (
                self.total_attempts(attempts)
            ),
            "successful_attempts": (
                self.successful_attempts(attempts)
            ),
            "failed_attempts": (
                self.failed_attempts(attempts)
            ),
            "predicted_revenue": (
                self.predicted_revenue(attempts)
            ),
            "actual_recovered_revenue": (
                self.actual_recovered_revenue(
                    attempts
                )
            ),
            "recovery_rate": (
                self.recovery_rate(attempts)
            ),
        }