from collections import Counter
from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
)

from backend.app.domain.models import (
    Payment,
)

from simulator.recovery.batch_runner import (
    BatchRecoveryResult,
)


@dataclass(frozen=True)
class RecoveryAnalyticsReport:
    """
    Immutable analytics report generated from
    payments and a completed batch recovery run.
    """

    total_payments: int
    total_failed_payments: int
    total_recovery_proposals: int

    successful_recoveries: int
    failed_recoveries: int
    unrecoverable_payments: int

    recovery_rate: float

    revenue_at_risk: Decimal
    recovered_revenue: Decimal
    unrecovered_revenue: Decimal

    failure_code_breakdown: dict[
        str,
        int,
    ]

    strategy_breakdown: dict[
        str,
        int,
    ]

    successful_strategy_breakdown: dict[
        str,
        int,
    ]

    failed_strategy_breakdown: dict[
        str,
        int,
    ]


class RecoveryAnalyticsReporter:
    """
    Builds measurable recovery analytics from
    the original payment batch and recovery
    execution results.
    """

    def build(
        self,
        *,
        payments: list[Payment],
        batch_result: BatchRecoveryResult,
    ) -> RecoveryAnalyticsReport:
        """
        Build a complete immutable analytics report.
        """

        failure_code_breakdown = Counter()

        strategy_breakdown = Counter()

        successful_strategy_breakdown = Counter()

        failed_strategy_breakdown = Counter()

        # -----------------------------------------
        # Failure-code breakdown
        # -----------------------------------------

        for payment in payments:

            if payment.failure_code is not None:

                failure_code_breakdown[
                    payment.failure_code
                ] += 1

        # -----------------------------------------
        # Strategy breakdown
        # -----------------------------------------

        for attempt in batch_result.attempts:

            strategy = attempt.strategy.value

            strategy_breakdown[
                strategy
            ] += 1

            if (
                attempt.status
                == RecoveryStatus.SUCCEEDED
            ):

                successful_strategy_breakdown[
                    strategy
                ] += 1

            elif (
                attempt.status
                == RecoveryStatus.FAILED
            ):

                failed_strategy_breakdown[
                    strategy
                ] += 1

        # -----------------------------------------
        # Revenue metrics
        # -----------------------------------------

        revenue_at_risk = (
            batch_result.total_revenue_at_risk
        )

        recovered_revenue = (
            batch_result.total_recovered_revenue
        )

        unrecovered_revenue = max(
            Decimal("0"),
            revenue_at_risk
            - recovered_revenue,
        )

        return RecoveryAnalyticsReport(
            total_payments=(
                batch_result.total_payments
            ),
            total_failed_payments=(
                batch_result.total_failed_payments
            ),
            total_recovery_proposals=(
                batch_result.total_recovery_proposals
            ),
            successful_recoveries=(
                batch_result.total_recovered
            ),
            failed_recoveries=(
                batch_result.total_failed_recoveries
            ),
            unrecoverable_payments=(
                batch_result.total_unrecoverable
            ),
            recovery_rate=(
                batch_result.recovery_rate
            ),
            revenue_at_risk=(
                revenue_at_risk
            ),
            recovered_revenue=(
                recovered_revenue
            ),
            unrecovered_revenue=(
                unrecovered_revenue
            ),
            failure_code_breakdown=dict(
                failure_code_breakdown
            ),
            strategy_breakdown=dict(
                strategy_breakdown
            ),
            successful_strategy_breakdown=dict(
                successful_strategy_breakdown
            ),
            failed_strategy_breakdown=dict(
                failed_strategy_breakdown
            ),
        )