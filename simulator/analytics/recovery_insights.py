from dataclasses import dataclass

from simulator.analytics.recovery_analytics import (
    RecoveryAnalyticsReport,
)


@dataclass(frozen=True)
class RecoveryInsight:
    """
    A single actionable insight generated from
    a completed recovery analytics report.
    """

    category: str

    message: str


@dataclass(frozen=True)
class RecoveryInsightsReport:
    """
    Collection of actionable insights generated
    from a recovery analytics report.
    """

    insights: list[RecoveryInsight]


class RecoveryInsights:
    """
    Generates actionable insights from completed
    RecoverX recovery analytics.

    This component is intentionally read-only.

    It does not modify:

    - recovery orchestration
    - recovery execution
    - escalation logic
    - batch processing
    - recovery metrics
    - recovery analytics

    It only interprets a completed
    RecoveryAnalyticsReport.
    """

    LOW_RECOVERY_RATE_THRESHOLD = 30.0

    HIGH_FAILURE_RATE_THRESHOLD = 30.0

    HIGH_APPROVAL_RATE_THRESHOLD = 50.0

    HIGH_ESCALATION_RATE_THRESHOLD = 50.0

    def analyze(
        self,
        *,
        report: RecoveryAnalyticsReport,
    ) -> RecoveryInsightsReport:
        """
        Generate actionable insights from a
        completed recovery analytics report.
        """

        insights: list[RecoveryInsight] = []

        # An empty batch has no operational
        # behaviour to interpret.
        if report.total_payments == 0:
            return RecoveryInsightsReport(
                insights=insights,
            )

        self._add_recovery_rate_insight(
            report=report,
            insights=insights,
        )

        self._add_failure_rate_insight(
            report=report,
            insights=insights,
        )

        self._add_approval_rate_insight(
            report=report,
            insights=insights,
        )

        self._add_escalation_rate_insight(
            report=report,
            insights=insights,
        )

        self._add_payment_method_insight(
            report=report,
            insights=insights,
        )

        return RecoveryInsightsReport(
            insights=insights,
        )

    # ============================================================
    # RECOVERY RATE
    # ============================================================

    def _add_recovery_rate_insight(
        self,
        *,
        report: RecoveryAnalyticsReport,
        insights: list[RecoveryInsight],
    ) -> None:
        """
        Add an insight when recovery performance
        falls below the configured threshold.
        """

        if (
            report.recovery_rate
            < self.LOW_RECOVERY_RATE_THRESHOLD
        ):
            insights.append(
                RecoveryInsight(
                    category="recovery_performance",
                    message=(
                        "Recovery performance requires "
                        "improvement."
                    ),
                )
            )

    # ============================================================
    # FAILURE RATE
    # ============================================================

    def _add_failure_rate_insight(
        self,
        *,
        report: RecoveryAnalyticsReport,
        insights: list[RecoveryInsight],
    ) -> None:
        """
        Add an insight when recovery execution
        failures are significantly high.
        """

        if (
            report.failure_rate
            >= self.HIGH_FAILURE_RATE_THRESHOLD
        ):
            insights.append(
                RecoveryInsight(
                    category="recovery_failures",
                    message=(
                        "Recovery execution failures are "
                        "significantly high."
                    ),
                )
            )

    # ============================================================
    # APPROVAL RATE
    # ============================================================

    def _add_approval_rate_insight(
        self,
        *,
        report: RecoveryAnalyticsReport,
        insights: list[RecoveryInsight],
    ) -> None:
        """
        Add an insight when a large proportion
        of recoveries require human approval.
        """

        if (
            report.approval_rate
            >= self.HIGH_APPROVAL_RATE_THRESHOLD
        ):
            insights.append(
                RecoveryInsight(
                    category="human_approval",
                    message=(
                        "A high proportion of recoveries "
                        "require human approval."
                    ),
                )
            )

    # ============================================================
    # ESCALATION RATE
    # ============================================================

    def _add_escalation_rate_insight(
        self,
        *,
        report: RecoveryAnalyticsReport,
        insights: list[RecoveryInsight],
    ) -> None:
        """
        Add an insight when recovery operations
        have a high dependency on escalation.
        """

        if (
            report.escalation_rate
            >= self.HIGH_ESCALATION_RATE_THRESHOLD
        ):
            insights.append(
                RecoveryInsight(
                    category="escalation",
                    message=(
                        "Recovery operations have a high "
                        "dependency on human escalation."
                    ),
                )
            )

    # ============================================================
    # PAYMENT METHOD PERFORMANCE
    # ============================================================

    def _add_payment_method_insight(
        self,
        *,
        report: RecoveryAnalyticsReport,
        insights: list[RecoveryInsight],
    ) -> None:
        """
        Identify the payment method with the
        highest recovery success rate.
        """

        success_rates = (
            report.success_rate_by_method
        )

        if not success_rates:
            return

        best_method = max(
            success_rates,
            key=lambda method: success_rates[
                method
            ],
        )

        best_rate = (
            success_rates[
                best_method
            ]
        )

        insights.append(
            RecoveryInsight(
                category="payment_method_performance",
                message=(
                    f"{best_method} demonstrates the "
                    f"strongest recovery performance "
                    f"at {best_rate:.2f}%."
                ),
            )
        )