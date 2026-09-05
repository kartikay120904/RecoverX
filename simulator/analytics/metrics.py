from dataclasses import dataclass
from decimal import Decimal

from simulator.simulation.batch_runner import (
    BatchRecoveryResult,
)


@dataclass(frozen=True)
class RecoveryMetrics:
    """
    Aggregated operational and financial metrics
    calculated from a completed recovery batch.
    """

    total_payments: int

    proposals_created: int
    executions_completed: int

    successful_recoveries: int
    failed_recoveries: int

    escalations_created: int

    total_payment_value: Decimal
    predicted_revenue: Decimal
    actual_recovered_revenue: Decimal

    recovery_success_rate: Decimal
    proposal_rate: Decimal


class RecoveryMetricsCalculator:
    """
    Calculates analytics from an existing
    BatchRecoveryResult.

    This component is read-only. It does not modify
    payments, recovery attempts, or workflow state.
    """

    def calculate(
        self,
        result: BatchRecoveryResult,
    ) -> RecoveryMetrics:

        # -----------------------------------------
        # Payment value
        # -----------------------------------------

        total_payment_value = sum(
            (
                payment.amount
                for payment in result.payments
            ),
            start=Decimal("0"),
        )

        # -----------------------------------------
        # Predicted revenue
        #
        # RecoveryAttempt already stores the
        # predicted revenue calculated during the
        # decision/proposal stage.
        #
        # Do not reconstruct it using positional
        # zip() relationships.
        # -----------------------------------------

        predicted_revenue = sum(
            (
                attempt.predicted_revenue
                for attempt in result.attempts
            ),
            start=Decimal("0"),
        )

        # -----------------------------------------
        # Actual recovered revenue
        #
        # actual_revenue may be None before a
        # completed execution, so handle it safely.
        # -----------------------------------------

        actual_recovered_revenue = sum(
            (
                attempt.actual_revenue
                if attempt.actual_revenue is not None
                else Decimal("0")
                for attempt in result.attempts
            ),
            start=Decimal("0"),
        )

        # -----------------------------------------
        # Recovery success rate
        # -----------------------------------------

        if result.executions_completed > 0:

            recovery_success_rate = (
                Decimal(
                    result.successful_recoveries
                )
                / Decimal(
                    result.executions_completed
                )
                * Decimal("100")
            )

        else:

            recovery_success_rate = Decimal("0")

        # -----------------------------------------
        # Proposal rate
        # -----------------------------------------

        if result.total_payments > 0:

            proposal_rate = (
                Decimal(
                    result.proposals_created
                )
                / Decimal(
                    result.total_payments
                )
                * Decimal("100")
            )

        else:

            proposal_rate = Decimal("0")

        return RecoveryMetrics(
            total_payments=(
                result.total_payments
            ),
            proposals_created=(
                result.proposals_created
            ),
            executions_completed=(
                result.executions_completed
            ),
            successful_recoveries=(
                result.successful_recoveries
            ),
            failed_recoveries=(
                result.failed_recoveries
            ),
            escalations_created=(
                result.escalations_created
            ),
            total_payment_value=(
                total_payment_value
            ),
            predicted_revenue=(
                predicted_revenue
            ),
            actual_recovered_revenue=(
                actual_recovered_revenue
            ),
            recovery_success_rate=(
                recovery_success_rate
            ),
            proposal_rate=(
                proposal_rate
            ),
        )