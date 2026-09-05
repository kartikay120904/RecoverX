from dataclasses import dataclass
from typing import Iterable

from backend.app.domain.enums import (
    RecoveryStatus,
)

from backend.app.domain.models import (
    Payment,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)


@dataclass(frozen=True)
class RecoveryAnalyticsReport:
    """
    Analytical summary generated from a completed
    RecoverX batch simulation.
    """

    total_payments: int

    recovery_rate: float

    failure_rate: float

    approval_rate: float

    escalation_rate: float

    revenue_recovered: float

    average_recovered_revenue: float

    success_rate_by_method: dict[
        str,
        float,
    ]

    success_rate_by_failure_code: dict[
        str,
        float,
    ]

    success_rate_by_strategy: dict[
        str,
        float,
    ]


class RecoveryAnalytics:
    """
    Generates analytical insights from completed
    recovery batch results.

    This component does not modify:

    - recovery orchestration
    - recovery execution
    - escalation logic
    - batch processing
    - recovery metrics

    It only reads completed simulation results.
    """

    def analyze(
        self,
        *,
        batch_result: RecoveryBatchResult,
        payments: Iterable[Payment] | None = None,
    ) -> RecoveryAnalyticsReport:
        """
        Analyze a completed recovery batch.
        """

        metrics = batch_result.metrics

        total_payments = (
            metrics.total_payments
        )

        recovery_rate = (
            metrics.recovery_rate
        )

        failure_rate = self._percentage(
            numerator=(
                metrics.failed_recoveries
            ),
            denominator=(
                metrics.recovery_attempts
            ),
        )

        approval_rate = self._percentage(
            numerator=(
                metrics.approval_required
            ),
            denominator=(
                total_payments
            ),
        )

        escalation_rate = self._percentage(
            numerator=(
                metrics.escalations
            ),
            denominator=(
                total_payments
            ),
        )

        average_recovered_revenue = (
            self._average_recovered_revenue(
                revenue=(
                    metrics.revenue_recovered
                ),
                successful_recoveries=(
                    metrics.successful_recoveries
                ),
            )
        )

        success_rate_by_method = (
            self._success_rate_by_method(
                results=(
                    batch_result.results
                ),
                payments=payments,
            )
        )

        success_rate_by_failure_code = (
            self._success_rate_by_failure_code(
                results=(
                    batch_result.results
                ),
                payments=payments,
            )
        )

        success_rate_by_strategy = (
            self._success_rate_by_strategy(
                results=(
                    batch_result.results
                ),
            )
        )

        return RecoveryAnalyticsReport(
            total_payments=total_payments,
            recovery_rate=recovery_rate,
            failure_rate=failure_rate,
            approval_rate=approval_rate,
            escalation_rate=escalation_rate,
            revenue_recovered=(
                metrics.revenue_recovered
            ),
            average_recovered_revenue=(
                average_recovered_revenue
            ),
            success_rate_by_method=(
                success_rate_by_method
            ),
            success_rate_by_failure_code=(
                success_rate_by_failure_code
            ),
            success_rate_by_strategy=(
                success_rate_by_strategy
            ),
        )

    def _success_rate_by_strategy(
        self,
        *,
        results,
    ) -> dict[str, float]:
        """
        Calculate recovery success rate grouped
        by recovery strategy.

        Strategy analytics is derived directly from
        recovery attempts and therefore does not
        require the original payment collection.
        """

        strategy_attempts: dict[
            str,
            int,
        ] = {}

        strategy_successes: dict[
            str,
            int,
        ] = {}

        for result in results:

            orchestration = (
                result.orchestration
            )

            attempt = (
                orchestration.attempt
            )

            if attempt is None:
                continue

            strategy = (
                getattr(
                    attempt,
                    "strategy",
                    None,
                )
            )

            if strategy is None:
                continue

            strategy_value = getattr(
                strategy,
                "value",
                strategy,
            )

            strategy_name = str(
                strategy_value
            )

            strategy_attempts[
                strategy_name
            ] = (
                strategy_attempts.get(
                    strategy_name,
                    0,
                )
                + 1
            )

            if (
                attempt.status
                == RecoveryStatus.SUCCEEDED
            ):

                strategy_successes[
                    strategy_name
                ] = (
                    strategy_successes.get(
                        strategy_name,
                        0,
                    )
                    + 1
                )

        return {
            strategy: self._percentage(
                numerator=(
                    strategy_successes.get(
                        strategy,
                        0,
                    )
                ),
                denominator=attempts,
            )
            for strategy, attempts
            in strategy_attempts.items()
        }

        

    def _percentage(
        self,
        *,
        numerator: int,
        denominator: int,
    ) -> float:
        """
        Calculate a percentage safely.
        """

        if denominator == 0:
            return 0.0

        return (
            numerator
            / denominator
        ) * 100

    def _average_recovered_revenue(
        self,
        *,
        revenue: float,
        successful_recoveries: int,
    ) -> float:
        """
        Calculate average recovered revenue
        per successful recovery.
        """

        if successful_recoveries == 0:
            return 0.0

        return (
            revenue
            / successful_recoveries
        )

    def _success_rate_by_method(
        self,
        *,
        results,
        payments: Iterable[Payment] | None,
    ) -> dict[str, float]:
        """
        Calculate recovery success rate grouped
        by normalized payment method.
        """

        if payments is None:
            return {}

        payment_by_id = {
            payment.payment_id: payment
            for payment in payments
        }

        method_attempts: dict[
            str,
            int,
        ] = {}

        method_successes: dict[
            str,
            int,
        ] = {}

        for result in results:

            orchestration = (
                result.orchestration
            )

            attempt = (
                orchestration.attempt
            )

            if attempt is None:
                continue

            payment = (
                payment_by_id.get(
                    attempt.payment_id
                )
            )

            if payment is None:
                continue

            method = (
                self._get_method_value(
                    payment
                )
            )

            method_attempts[
                method
            ] = (
                method_attempts.get(
                    method,
                    0,
                )
                + 1
            )

            if (
                attempt.status
                == RecoveryStatus.SUCCEEDED
            ):

                method_successes[
                    method
                ] = (
                    method_successes.get(
                        method,
                        0,
                    )
                    + 1
                )

        return {
            method: self._percentage(
                numerator=(
                    method_successes.get(
                        method,
                        0,
                    )
                ),
                denominator=attempts,
            )
            for method, attempts
            in method_attempts.items()
        }

    def _get_method_value(
        self,
        payment: Payment,
    ) -> str:
        """
        Normalize the payment method into a stable
        string value for analytics reporting.

        Supports both enum-based and string-based
        payment methods.
        """

        method = payment.method

        value = getattr(
            method,
            "value",
            method,
        )

        return str(
            value
        )

    def _success_rate_by_failure_code(
        self,
        *,
        results,
        payments: Iterable[Payment] | None,
    ) -> dict[str, float]:
        """
        Calculate recovery success rate grouped
        by payment failure code.
        """

        if payments is None:
            return {}

        payment_by_id = {
            payment.payment_id: payment
            for payment in payments
        }

        failure_attempts: dict[
            str,
            int,
        ] = {}

        failure_successes: dict[
            str,
            int,
        ] = {}

        for result in results:

            orchestration = (
                result.orchestration
            )

            attempt = (
                orchestration.attempt
            )

            if attempt is None:
                continue

            payment = (
                payment_by_id.get(
                    attempt.payment_id
                )
            )

            if payment is None:
                continue

            failure_code = (
                payment.failure_code
            )

            if failure_code is None:
                continue

            failure_code = str(
                failure_code
            )

            failure_attempts[
                failure_code
            ] = (
                failure_attempts.get(
                    failure_code,
                    0,
                )
                + 1
            )

            if (
                attempt.status
                == RecoveryStatus.SUCCEEDED
            ):

                failure_successes[
                    failure_code
                ] = (
                    failure_successes.get(
                        failure_code,
                        0,
                    )
                    + 1
                )

        return {
            failure_code: self._percentage(
                numerator=(
                    failure_successes.get(
                        failure_code,
                        0,
                    )
                ),
                denominator=attempts,
            )
            for failure_code, attempts
            in failure_attempts.items()
        }