from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)


class RecoveryBatchReporter:
    """
    Formats RecoverX batch recovery metrics into
    a human-readable report.

    This class does not modify recovery,
    escalation, orchestration, or metric logic.

    It only presents the aggregated results.
    """

    def render(
        self,
        result: RecoveryBatchResult,
    ) -> str:
        """
        Render a complete batch recovery report.
        """

        metrics = result.metrics

        return "\n".join(
            [
                "=" * 52,
                "RECOVERX — REVENUE RECOVERY BATCH REPORT",
                "=" * 52,
                "",
                (
                    "Total Payments Processed: "
                    f"{metrics.total_payments}"
                ),
                (
                    "Payments Flagged: "
                    f"{metrics.payments_flagged}"
                ),
                (
                    "Recovery Attempts: "
                    f"{metrics.recovery_attempts}"
                ),
                "",
                (
                    "Successful Recoveries: "
                    f"{metrics.successful_recoveries}"
                ),
                (
                    "Failed Recoveries: "
                    f"{metrics.failed_recoveries}"
                ),
                (
                    "Blocked Recoveries: "
                    f"{metrics.blocked_recoveries}"
                ),
                "",
                (
                    "Approval Required: "
                    f"{metrics.approval_required}"
                ),
                (
                    "Escalations: "
                    f"{metrics.escalations}"
                ),
                "",
                (
                    "Revenue Recovered: "
                    f"₹{metrics.revenue_recovered:,.2f}"
                ),
                (
                    "Recovery Rate: "
                    f"{metrics.recovery_rate:.2f}%"
                ),
                "=" * 52,
            ]
        )