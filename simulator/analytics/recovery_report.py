from dataclasses import dataclass
from decimal import Decimal

from simulator.analytics.recovery_dashboard import (
    RecoveryDashboard,
)


@dataclass(frozen=True)
class RecoveryReport:
    """
    Serializable summary of recovery analytics.
    """

    total_actions: int

    high_priority_actions: int
    medium_priority_actions: int
    low_priority_actions: int

    total_attempts: int
    successful_attempts: int
    failed_attempts: int

    recovery_rate: float

    predicted_revenue: Decimal
    actual_recovered_revenue: Decimal
    recovery_opportunity: Decimal

    best_strategy: str | None


class RecoveryReportBuilder:
    """
    Converts a RecoveryDashboard into a compact
    analytics report.
    """

    def build(
        self,
        *,
        dashboard: RecoveryDashboard,
    ) -> RecoveryReport:

        action_plan = dashboard.action_plan
        impact = dashboard.impact

        best_strategy = (
            impact.best_strategy.value
            if impact.best_strategy is not None
            else None
        )

        return RecoveryReport(
            total_actions=action_plan.total_actions,

            high_priority_actions=len(
                action_plan.high_priority_actions
            ),
            medium_priority_actions=len(
                action_plan.medium_priority_actions
            ),
            low_priority_actions=len(
                action_plan.low_priority_actions
            ),

            total_attempts=impact.total_attempts,
            successful_attempts=impact.successful_attempts,
            failed_attempts=impact.failed_attempts,

            recovery_rate=impact.recovery_rate,

            predicted_revenue=impact.predicted_revenue,
            actual_recovered_revenue=(
                impact.actual_recovered_revenue
            ),
            recovery_opportunity=(
                impact.recovery_opportunity
            ),

            best_strategy=best_strategy,
        )