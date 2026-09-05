from dataclasses import dataclass

from backend.app.domain.models import RecoveryAttempt

from simulator.analytics.recovery_action_plan import (
    RecoveryActionPlan,
)
from simulator.analytics.recovery_impact import (
    RecoveryImpact,
    calculate_recovery_impact,
)
from simulator.analytics.recovery_pipeline import (
    RecoveryPipeline,
)


@dataclass(frozen=True)
class RecoveryDashboard:
    """
    Combined recovery decision and performance view.
    """

    action_plan: RecoveryActionPlan
    impact: RecoveryImpact


class RecoveryDashboardBuilder:
    """
    Builds a unified recovery analytics result without
    modifying existing analytics components.
    """

    def __init__(
        self,
        *,
        pipeline: RecoveryPipeline | None = None,
    ) -> None:

        self._pipeline = (
            pipeline
            or RecoveryPipeline()
        )

    def build(
        self,
        *,
        insights: list,
        attempts: list[RecoveryAttempt],
    ) -> RecoveryDashboard:
        """
        Combine recommended actions with measured
        recovery performance.
        """

        action_plan = (
            self._pipeline.run(
                insights=insights,
            )
        )

        impact = (
            calculate_recovery_impact(
                attempts=attempts,
            )
        )

        return RecoveryDashboard(
            action_plan=action_plan,
            impact=impact,
        )