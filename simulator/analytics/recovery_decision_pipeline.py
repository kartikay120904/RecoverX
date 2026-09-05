from dataclasses import dataclass

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


@dataclass(frozen=True)
class RecoveryDecisionResult:
    """
    Result of the recovery decision pipeline.
    """

    recommendations: tuple[
        RecoveryRecommendation,
        ...
    ]

    action_plan: RecoveryActionPlan


class RecoveryDecisionPipeline:
    """
    Orchestrates recovery insights into prioritized
    recovery recommendations and an execution-ready
    action plan.
    """

    def __init__(
        self,
        *,
        recommendation_generator: (
            RecoveryRecommendations | None
        ) = None,
        prioritizer: (
            RecoveryRecommendationPrioritizer | None
        ) = None,
        action_plan_builder: (
            RecoveryActionPlanBuilder | None
        ) = None,
    ) -> None:

        self._recommendation_generator = (
            recommendation_generator
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

    def run(
        self,
        *,
        insights: list,
    ) -> RecoveryDecisionResult:
        """
        Generate, prioritize, and convert recovery
        recommendations into an action plan.
        """

        recommendations = (
            self._recommendation_generator.generate(
                insights=insights,
            )
        )

        prioritized = (
            self._prioritizer.prioritize(
                recommendations=recommendations,
            )
        )

        action_plan = (
            self._action_plan_builder.build(
                recommendations=prioritized,
            )
        )

        return RecoveryDecisionResult(
            recommendations=tuple(
                prioritized
            ),
            action_plan=action_plan,
        )