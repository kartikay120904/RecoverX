from simulator.analytics.recovery_action_plan import (
    RecoveryActionPlan,
    RecoveryActionPlanBuilder,
)
from simulator.analytics.recovery_prioritizer import (
    RecoveryRecommendationPrioritizer,
)
from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
    RecoveryRecommendations,
)


class RecoveryAnalyticsPipeline:
    """
    Orchestrates recovery analytics recommendations
    into a prioritized execution-ready action plan.
    """

    def __init__(
        self,
        *,
        recommendations: RecoveryRecommendations | None = None,
        prioritizer: (
            RecoveryRecommendationPrioritizer | None
        ) = None,
        action_plan_builder: (
            RecoveryActionPlanBuilder | None
        ) = None,
    ) -> None:

        self._recommendations = (
            recommendations
            or RecoveryRecommendations()
        )

        self._prioritizer = (
            prioritizer
            or RecoveryRecommendationPrioritizer()
        )

        self._action_plan_builder = (
            action_plan_builder
            or RecoveryActionPlanBuilder()
        )

    def build_action_plan(
        self,
        *,
        insights: list,
    ) -> RecoveryActionPlan:
        """
        Generate recommendations from insights,
        prioritize them, and build an immutable
        recovery action plan.
        """

        recommendations = (
            self._recommendations.generate(
                insights=insights,
            )
        )

        prioritized = (
            self._prioritizer.prioritize(
                recommendations=recommendations,
            )
        )

        return (
            self._action_plan_builder.build(
                recommendations=prioritized,
            )
        )

    def run(
        self,
        *,
        insights: list,
    ) -> RecoveryActionPlan:
        """
        Backward-compatible pipeline entry point.

        Generate recommendations, prioritize them,
        and return an immutable recovery action plan.
        """

        return self.build_action_plan(
            insights=insights,
        )


# Backward-compatible name expected by
# existing dashboard and report modules.
RecoveryPipeline = RecoveryAnalyticsPipeline