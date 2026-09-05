from dataclasses import dataclass


@dataclass
class RecoveryMetrics:
    """
    Aggregates metrics produced by a RecoverX
    batch recovery simulation.

    This class is intentionally independent from
    recovery, escalation, policy, and execution
    implementations.

    It only records outcomes produced by those
    components.
    """

    total_payments: int = 0

    payments_flagged: int = 0

    recovery_attempts: int = 0

    successful_recoveries: int = 0

    failed_recoveries: int = 0

    blocked_recoveries: int = 0

    approval_required: int = 0

    escalations: int = 0

    revenue_recovered: float = 0.0

    @property
    def recovery_rate(self) -> float:
        """
        Calculate the percentage of recovery attempts
        that successfully recovered revenue.
        """

        if self.recovery_attempts == 0:
            return 0.0

        return (
            self.successful_recoveries
            / self.recovery_attempts
        ) * 100

    def record_payment(self) -> None:
        """Record one processed payment."""

        self.total_payments += 1

    def record_flagged_payment(self) -> None:
        """Record a payment flagged for recovery."""

        self.payments_flagged += 1

    def record_recovery_attempt(self) -> None:
        """Record a recovery attempt."""

        self.recovery_attempts += 1

    def record_success(
        self,
        revenue: float = 0.0,
    ) -> None:
        """
        Record a successful recovery and
        aggregate recovered revenue.
        """

        self.successful_recoveries += 1

        self.revenue_recovered += float(
            revenue
        )

    def record_failure(self) -> None:
        """Record a failed recovery."""

        self.failed_recoveries += 1

    def record_blocked(self) -> None:
        """Record a blocked recovery."""

        self.blocked_recoveries += 1

    def record_approval_required(self) -> None:
        """Record a recovery requiring approval."""

        self.approval_required += 1

    def record_escalation(self) -> None:
        """Record an escalation."""

        self.escalations += 1