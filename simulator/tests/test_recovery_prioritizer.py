from simulator.analytics.recovery_prioritizer import (
    RecoveryRecommendationPrioritizer,
)
from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
)


def create_recommendation(
    *,
    category: str,
    priority: str,
) -> RecoveryRecommendation:

    return RecoveryRecommendation(
        category=category,
        priority=priority,
        reason="Test recommendation.",
    )


def test_empty_recommendations_remain_empty():

    recommendations = (
        RecoveryRecommendationPrioritizer().prioritize(
            recommendations=[],
        )
    )

    assert recommendations == []


def test_high_priority_comes_before_medium():

    recommendations = [
        create_recommendation(
            category="best_strategy",
            priority="medium",
        ),
        create_recommendation(
            category="low_recovery_rate",
            priority="high",
        ),
    ]

    prioritized = (
        RecoveryRecommendationPrioritizer().prioritize(
            recommendations=recommendations,
        )
    )

    assert (
        prioritized[0].priority
        == "high"
    )

    assert (
        prioritized[1].priority
        == "medium"
    )


def test_high_medium_low_priority_order():

    recommendations = [
        create_recommendation(
            category="low",
            priority="low",
        ),
        create_recommendation(
            category="medium",
            priority="medium",
        ),
        create_recommendation(
            category="high",
            priority="high",
        ),
    ]

    prioritized = (
        RecoveryRecommendationPrioritizer().prioritize(
            recommendations=recommendations,
        )
    )

    priorities = [
        recommendation.priority
        for recommendation
        in prioritized
    ]

    assert priorities == [
        "high",
        "medium",
        "low",
    ]


def test_unknown_priority_goes_last():

    recommendations = [
        create_recommendation(
            category="unknown",
            priority="unknown",
        ),
        create_recommendation(
            category="high",
            priority="high",
        ),
    ]

    prioritized = (
        RecoveryRecommendationPrioritizer().prioritize(
            recommendations=recommendations,
        )
    )

    assert (
        prioritized[0].priority
        == "high"
    )

    assert (
        prioritized[1].priority
        == "unknown"
    )


def test_original_recommendations_are_not_modified():

    recommendations = [
        create_recommendation(
            category="medium",
            priority="medium",
        ),
        create_recommendation(
            category="high",
            priority="high",
        ),
    ]

    original_order = list(recommendations)

    RecoveryRecommendationPrioritizer().prioritize(
        recommendations=recommendations,
    )

    assert recommendations == original_order