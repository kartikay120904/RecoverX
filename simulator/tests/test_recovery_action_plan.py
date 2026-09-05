from simulator.analytics.recovery_action_plan import (
    RecoveryActionPlan,
    RecoveryActionPlanBuilder,
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


def test_empty_recommendations_create_empty_plan():

    plan = (
        RecoveryActionPlanBuilder().build(
            recommendations=[],
        )
    )

    assert isinstance(
        plan,
        RecoveryActionPlan,
    )

    assert plan.total_actions == 0

    assert plan.recommendations == ()


def test_plan_contains_all_recommendations():

    recommendations = [
        create_recommendation(
            category="low_recovery_rate",
            priority="high",
        ),
        create_recommendation(
            category="best_strategy",
            priority="medium",
        ),
    ]

    plan = (
        RecoveryActionPlanBuilder().build(
            recommendations=recommendations,
        )
    )

    assert plan.total_actions == 2


def test_high_priority_actions_are_filtered():

    recommendations = [
        create_recommendation(
            category="low_recovery_rate",
            priority="high",
        ),
        create_recommendation(
            category="best_strategy",
            priority="medium",
        ),
        create_recommendation(
            category="high_failure_rate",
            priority="high",
        ),
    ]

    plan = (
        RecoveryActionPlanBuilder().build(
            recommendations=recommendations,
        )
    )

    assert len(
        plan.high_priority_actions
    ) == 2


def test_medium_priority_actions_are_filtered():

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

    plan = (
        RecoveryActionPlanBuilder().build(
            recommendations=recommendations,
        )
    )

    assert len(
        plan.medium_priority_actions
    ) == 1


def test_low_priority_actions_are_filtered():

    recommendations = [
        create_recommendation(
            category="test",
            priority="low",
        ),
        create_recommendation(
            category="critical",
            priority="high",
        ),
    ]

    plan = (
        RecoveryActionPlanBuilder().build(
            recommendations=recommendations,
        )
    )

    assert len(
        plan.low_priority_actions
    ) == 1


def test_plan_is_immutable():

    plan = RecoveryActionPlan(
        recommendations=(),
    )

    try:
        plan.recommendations = ()
        assert False
    except Exception:
        assert True


def test_builder_does_not_modify_input_list():

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

    original = list(
        recommendations
    )

    RecoveryActionPlanBuilder().build(
        recommendations=recommendations,
    )

    assert recommendations == original