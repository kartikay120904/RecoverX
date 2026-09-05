from dataclasses import dataclass

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)


@dataclass(frozen=True)
class RecoverySimulationReport:
    """
    Read-only summary of a completed RecoverX
    recovery simulation.

    This object is created from an existing
    RecoveryBatchResult and does not modify
    simulation or recovery state.
    """

    total_payments: int

    payments_flagged: int

    recovery_attempts: int

    successful_recoveries: int

    failed_recoveries: int

    blocked_recoveries: int

    approval_required: int

    escalations: int

    revenue_recovered: float

    recovery_rate: float

    @classmethod
    def from_batch_result(
        cls,
        batch_result: RecoveryBatchResult,
    ) -> "RecoverySimulationReport":
        """
        Create a report from an existing batch result.
        """

        metrics = (
            batch_result.metrics
        )

        return cls(
            total_payments=(
                metrics.total_payments
            ),
            payments_flagged=(
                metrics.payments_flagged
            ),
            recovery_attempts=(
                metrics.recovery_attempts
            ),
            successful_recoveries=(
                metrics.successful_recoveries
            ),
            failed_recoveries=(
                metrics.failed_recoveries
            ),
            blocked_recoveries=(
                metrics.blocked_recoveries
            ),
            approval_required=(
                metrics.approval_required
            ),
            escalations=(
                metrics.escalations
            ),
            revenue_recovered=(
                metrics.revenue_recovered
            ),
            recovery_rate=(
                metrics.recovery_rate
            ),
        )

    @property
    def unsuccessful_recoveries(
        self,
    ) -> int:
        return (
            self.recovery_attempts
            - self.successful_recoveries
        )

    @property
    def average_revenue_per_success(
        self,
    ) -> float:

        if self.successful_recoveries == 0:
            return 0.0

        return (
            self.revenue_recovered
            / self.successful_recoveries
        )

    @property
    def payment_flag_rate(
        self,
    ) -> float:

        if self.total_payments == 0:
            return 0.0

        return (
            self.payments_flagged
            / self.total_payments
        ) * 100

    @property
    def escalation_rate(
        self,
    ) -> float:

        if self.total_payments == 0:
            return 0.0

        return (
            self.escalations
            / self.total_payments
        ) * 100