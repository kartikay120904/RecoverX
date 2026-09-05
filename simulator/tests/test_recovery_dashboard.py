from dataclasses import dataclass

from simulator.analytics.recovery_dashboard import (
    RecoveryDashboard,
    RecoveryDashboardBuilder,
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


def test_dashboard_contains_action_plan_and_impact():

    dashboard = (
        RecoveryDashboardBuilder().build(
            insights=[],
            attempts=[],
        )
    )

    assert isinstance(
        dashboard,
        RecoveryDashboard,
    )

    assert (
        dashboard.action_plan.total_actions
        == 0
    )

    assert (
        dashboard.impact.total_attempts
        == 0
    )


def test_dashboard_builds_actions_from_insights():

    insights = [
        create_insight(
            category="low_recovery_rate",
        ),
    ]

    dashboard = (
        RecoveryDashboardBuilder().build(
            insights=insights,
            attempts=[],
        )
    )

    assert (
        dashboard.action_plan.total_actions
        == 1
    )

    assert (
        dashboard.action_plan
        .recommendations[0]
        .category
        == "low_recovery_rate"
    )


def test_dashboard_calculates_empty_recovery_impact():

    dashboard = (
        RecoveryDashboardBuilder().build(
            insights=[],
            attempts=[],
        )
    )

    impact = dashboard.impact

    assert impact.total_attempts == 0
    assert impact.successful_attempts == 0
    assert impact.failed_attempts == 0
    assert impact.recovery_rate == 0.0