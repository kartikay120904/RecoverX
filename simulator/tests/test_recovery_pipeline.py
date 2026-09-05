from dataclasses import dataclass

from simulator.analytics.recovery_pipeline import (
    RecoveryAnalyticsPipeline,
)


@dataclass(frozen=True)
class StubInsight:
    """
    Minimal insight used to test the
    recovery analytics pipeline.
    """

    category: str
    message: str = ""


def create_insight(
    *,
    category: str,
    message: str = "Test insight.",
) -> StubInsight:

    return StubInsight(
        category=category,
        message=message,
    )


def test_empty_insights_produce_empty_action_plan():

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=[],
        )
    )

    assert action_plan.total_actions == 0

    assert action_plan.recommendations == ()


def test_single_insight_produces_action_plan():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
    ]

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    assert action_plan.total_actions == 1

    assert (
        action_plan.recommendations[0].category
        == "low_recovery_rate"
    )


def test_recommendations_are_prioritized():

    insights = [
        create_insight(
            category="best_strategy",
        ),
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_approval_rate",
        ),
        create_insight(
            category="high_failure_rate",
        ),
    ]

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    priorities = [
        recommendation.priority
        for recommendation
        in action_plan.recommendations
    ]

    assert priorities == [
        "high",
        "high",
        "medium",
        "medium",
    ]


def test_high_priority_actions_are_exposed():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="best_strategy",
        ),
        create_insight(
            category="high_failure_rate",
        ),
    ]

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    assert (
        len(
            action_plan.high_priority_actions
        )
        == 2
    )


def test_unknown_insights_are_excluded():

    insights = [
        create_insight(
            category="unknown_category",
        ),
    ]

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    assert action_plan.total_actions == 0


def test_duplicate_categories_produce_one_action():

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

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    assert action_plan.total_actions == 1

    assert (
        action_plan.recommendations[0].reason
        == "First."
    )


def test_action_plan_is_immutable():

    insights = [
        create_insight(
            category="best_strategy",
        ),
    ]

    action_plan = (
        RecoveryAnalyticsPipeline().build_action_plan(
            insights=insights,
        )
    )

    assert isinstance(
        action_plan.recommendations,
        tuple,
    )