from dataclasses import dataclass

from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
    RecoveryRecommendations,
)


@dataclass(frozen=True)
class StubInsight:
    """
    Minimal insight object used to test
    recommendations independently from the
    insight implementation.
    """

    category: str

    message: str = ""


def create_insight(
    *,
    category: str,
    message: str = "Test insight.",
) -> StubInsight:
    """
    Create a deterministic insight for
    recommendation tests.
    """

    return StubInsight(
        category=category,
        message=message,
    )

def generate(
    self,
    *,
    insights: list,
) -> list[RecoveryRecommendation]:

    recommendations = []

    seen_categories = set()

    category_mapping = {
        "low_recovery_rate": {
            "action": "improve_recovery_strategy",
            "reason": (
                "Recovery rate is low. Review and improve "
                "the payment recovery strategy."
            ),
        },
        "high_failure_rate": {
            "action": "reduce_payment_failures",
            "reason": (
                "Payment failure rate is high. Investigate "
                "failure causes and improve payment reliability."
            ),
        },
        "high_approval_rate": {
            "action": "maintain_payment_strategy",
            "reason": (
                "Payment approval rate is high. Continue "
                "monitoring the current payment strategy."
            ),
        },
        "high_escalation_rate": {
            "action": "review_escalation_process",
            "reason": (
                "Escalation rate is high. Review the recovery "
                "and escalation process."
            ),
        },
        "best_payment_method": {
            "action": "promote_best_payment_method",
            "reason": (
                "A payment method is performing better than "
                "others. Consider prioritizing it."
            ),
        },
        "best_failure_code": {
            "action": "optimize_failure_handling",
            "reason": (
                "A dominant failure pattern was identified. "
                "Optimize recovery handling for it."
            ),
        },
        "best_strategy": {
            "action": "use_best_recovery_strategy",
            "reason": (
                "A recovery strategy is performing best. "
                "Consider prioritizing it."
            ),
        },
    }

    for insight in insights:

        category = insight.category

        if category in seen_categories:
            continue

        config = category_mapping.get(category)

        if config is None:
            continue

        seen_categories.add(category)

        reason = insight.message or config["reason"]

        recommendations.append(
            RecoveryRecommendation(
                category=category,
                action=config["action"],
                reason=reason,
            )
        )

    return recommendations


def test_empty_insights_produce_no_recommendations():

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[],
        )
    )

    assert recommendations == []


def test_low_recovery_rate_recommendation():

    insight = create_insight(
        category="low_recovery_rate",
        message="Recovery rate is low.",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    recommendation = recommendations[0]

    assert (
        recommendation.category
        == "low_recovery_rate"
    )

    assert (
        recommendation.priority
        == "high"
    )

    assert (
        recommendation.reason
        == "Recovery rate is low."
    )


def test_high_failure_rate_recommendation():

    insight = create_insight(
        category="high_failure_rate",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].priority
        == "high"
    )


def test_high_approval_rate_recommendation():

    insight = create_insight(
        category="high_approval_rate",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].priority
        == "medium"
    )


def test_high_escalation_rate_recommendation():

    insight = create_insight(
        category="high_escalation_rate",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].priority
        == "high"
    )


def test_best_payment_method_recommendation():

    insight = create_insight(
        category="best_payment_method",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].category
        == "best_payment_method"
    )


def test_best_failure_code_recommendation():

    insight = create_insight(
        category="best_failure_code",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].category
        == "best_failure_code"
    )


def test_best_strategy_recommendation():

    insight = create_insight(
        category="best_strategy",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].category
        == "best_strategy"
    )


def test_unknown_category_produces_no_recommendation():

    insight = create_insight(
        category="unknown_category",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert recommendations == []


def test_duplicate_categories_produce_one_recommendation():

    insights = [
        create_insight(
            category="low_recovery_rate",
            message="First.",
        ),
        create_insight(
            category="low_recovery_rate",
            message="Second.",
        ),
    ]

    recommendations = (
        RecoveryRecommendations().generate(
            insights=insights,
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].reason
        == "First."
    )


def test_multiple_insights_produce_multiple_recommendations():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_failure_rate",
        ),
        create_insight(
            category="best_strategy",
        ),
    ]

    recommendations = (
        RecoveryRecommendations().generate(
            insights=insights,
        )
    )

    assert len(
        recommendations
    ) == 3


def test_recommendation_categories_are_unique():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_failure_rate",
        ),
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_escalation_rate",
        ),
    ]

    recommendations = (
        RecoveryRecommendations().generate(
            insights=insights,
        )
    )

    categories = [
        recommendation.category
        for recommendation
        in recommendations
    ]

    assert len(
        categories
    ) == len(
        set(categories)
    )


def test_reason_falls_back_when_message_is_empty():

    insight = create_insight(
        category="best_strategy",
        message="",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert len(
        recommendations
    ) == 1

    assert (
        recommendations[0].reason
        == (
            "Recovery insight detected for "
            "category 'best_strategy'."
        )
    )


def test_recommendations_are_recovery_recommendation_objects():

    insight = create_insight(
        category="low_recovery_rate",
    )

    recommendations = (
        RecoveryRecommendations().generate(
            insights=[insight],
        )
    )

    assert isinstance(
        recommendations[0],
        RecoveryRecommendation,
    )

