from decimal import Decimal

from simulator.analytics.recovery_action_plan import (
    RecoveryActionPlan,
)
from simulator.analytics.recovery_dashboard import (
    RecoveryDashboard,
)
from simulator.analytics.recovery_impact import (
    RecoveryImpact,
)
from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendation,
)
from simulator.analytics.recovery_report import (
    RecoveryReport,
    RecoveryReportBuilder,
)


def create_dashboard() -> RecoveryDashboard:

    recommendations = (
        RecoveryRecommendation(
            category="low_recovery_rate",
            priority="high",
            reason="Recovery rate is low.",
        ),
        RecoveryRecommendation(
            category="best_strategy",
            priority="medium",
            reason="A strategy is performing well.",
        ),
    )

    action_plan = RecoveryActionPlan(
        recommendations=recommendations,
    )

    impact = RecoveryImpact(
        total_attempts=10,
        successful_attempts=6,
        failed_attempts=4,
        predicted_revenue=Decimal("1000"),
        actual_recovered_revenue=Decimal("600"),
        recovery_rate=0.6,
        recovery_opportunity=Decimal("400"),
        attempts_by_strategy={},
        recovered_revenue_by_strategy={},
        best_strategy=None,
    )

    return RecoveryDashboard(
        action_plan=action_plan,
        impact=impact,
    )


def test_report_is_created():

    dashboard = create_dashboard()

    report = (
        RecoveryReportBuilder().build(
            dashboard=dashboard,
        )
    )

    assert isinstance(
        report,
        RecoveryReport,
    )


def test_report_contains_action_counts():

    report = (
        RecoveryReportBuilder().build(
            dashboard=create_dashboard(),
        )
    )

    assert report.total_actions == 2
    assert report.high_priority_actions == 1
    assert report.medium_priority_actions == 1
    assert report.low_priority_actions == 0


def test_report_contains_recovery_metrics():

    report = (
        RecoveryReportBuilder().build(
            dashboard=create_dashboard(),
        )
    )

    assert report.total_attempts == 10
    assert report.successful_attempts == 6
    assert report.failed_attempts == 4
    assert report.recovery_rate == 0.6


def test_report_contains_revenue_metrics():

    report = (
        RecoveryReportBuilder().build(
            dashboard=create_dashboard(),
        )
    )

    assert (
        report.predicted_revenue
        == Decimal("1000")
    )

    assert (
        report.actual_recovered_revenue
        == Decimal("600")
    )

    assert (
        report.recovery_opportunity
        == Decimal("400")
    )


def test_report_best_strategy_is_none_when_missing():

    report = (
        RecoveryReportBuilder().build(
            dashboard=create_dashboard(),
        )
    )

    assert report.best_strategy is None