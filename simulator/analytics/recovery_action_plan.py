from dataclasses import dataclass

from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
)


@dataclass(frozen=True)
class RecoveryActionPlan:
    """
    Execution-ready action plan generated from
    prioritized recovery recommendations.
    """

    recommendations: tuple[RecoveryRecommendation, ...]

    @property
    def total_actions(self) -> int:
        return len(
            self.recommendations
        )

    @property
    def high_priority_actions(self) -> tuple[
        RecoveryRecommendation,
        ...
    ]:
        return tuple(
            recommendation
            for recommendation
            in self.recommendations
            if recommendation.priority == "high"
        )

    @property
    def medium_priority_actions(self) -> tuple[
        RecoveryRecommendation,
        ...
    ]:
        return tuple(
            recommendation
            for recommendation
            in self.recommendations
            if recommendation.priority == "medium"
        )

    @property
    def low_priority_actions(self) -> tuple[
        RecoveryRecommendation,
        ...
    ]:
        return tuple(
            recommendation
            for recommendation
            in self.recommendations
            if recommendation.priority == "low"
        )


class RecoveryActionPlanBuilder:
    """
    Build an immutable recovery action plan from
    prioritized recommendations.
    """

    def build(
        self,
        *,
        recommendations: list[RecoveryRecommendation],
    ) -> RecoveryActionPlan:

        return RecoveryActionPlan(
            recommendations=tuple(
                recommendations
            ),
        )