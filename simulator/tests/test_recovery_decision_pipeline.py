from dataclasses import dataclass

from simulator.analytics.recovery_decision_pipeline import (
    RecoveryDecisionPipeline,
    RecoveryDecisionResult,
)


@dataclass(frozen=True)
class StubInsight:
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


def test_empty_insights_produce_empty_result():

    result = (
        RecoveryDecisionPipeline().run(
            insights=[],
        )
    )

    assert isinstance(
        result,
        RecoveryDecisionResult,
    )

    assert result.recommendations == ()

    assert (
        result.action_plan.total_actions
        == 0
    )


def test_pipeline_generates_recommendations():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    assert len(
        result.recommendations
    ) == 1

    assert (
        result.recommendations[0].category
        == "low_recovery_rate"
    )


def test_pipeline_prioritizes_recommendations():

    insights = [
        create_insight(
            category="best_strategy",
        ),
        create_insight(
            category="low_recovery_rate",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    assert (
        result.recommendations[0].priority
        == "high"
    )

    assert (
        result.recommendations[1].priority
        == "medium"
    )


def test_pipeline_builds_action_plan():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_failure_rate",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    assert (
        result.action_plan.total_actions
        == 2
    )


def test_action_plan_matches_recommendations():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="best_strategy",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    assert (
        result.action_plan.recommendations
        == result.recommendations
    )


def test_pipeline_ignores_unknown_insights():

    insights = [
        create_insight(
            category="unknown_category",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    assert result.recommendations == ()

    assert (
        result.action_plan.total_actions
        == 0
    )


def test_pipeline_preserves_unique_categories():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="low_recovery_rate",
        ),
        create_insight(
            category="high_failure_rate",
        ),
    ]

    result = (
        RecoveryDecisionPipeline().run(
            insights=insights,
        )
    )

    categories = [
        recommendation.category
        for recommendation
        in result.recommendations
    ]

    assert len(
        categories
    ) == len(
        set(categories)
    )