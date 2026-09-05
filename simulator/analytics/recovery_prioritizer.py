from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
)


class RecoveryRecommendationPrioritizer:
    """
    Prioritize recovery recommendations based on severity.
    """

    _priority_order = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    def prioritize(
        self,
        *,
        recommendations: list[RecoveryRecommendation],
    ) -> list[RecoveryRecommendation]:

        return sorted(
            recommendations,
            key=lambda recommendation: (
                self._priority_order.get(
                    recommendation.priority,
                    999,
                ),
                recommendation.category or "",
            ),
        )