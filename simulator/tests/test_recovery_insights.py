from simulator.analytics.recovery_analytics import (
    RecoveryAnalyticsReport,
)

from simulator.analytics.recovery_insights import (
    RecoveryInsights,
)


def create_report(
    *,
    total_payments: int = 0,
    recovery_rate: float = 0.0,
    failure_rate: float = 0.0,
    approval_rate: float = 0.0,
    escalation_rate: float = 0.0,
    revenue_recovered: float = 0.0,
    average_recovered_revenue: float = 0.0,
    success_rate_by_method: (
        dict[str, float] | None
    ) = None,
    success_rate_by_failure_code: (
        dict[str, float] | None
    ) = None,
    success_rate_by_strategy: (
        dict[str, float] | None
    ) = None,
) -> RecoveryAnalyticsReport:
    """
    Create a deterministic analytics report
    for insight tests.
    """

    return RecoveryAnalyticsReport(
        total_payments=total_payments,
        recovery_rate=recovery_rate,
        failure_rate=failure_rate,
        approval_rate=approval_rate,
        escalation_rate=escalation_rate,
        revenue_recovered=revenue_recovered,
        average_recovered_revenue=(
            average_recovered_revenue
        ),
        success_rate_by_method=(
            success_rate_by_method
            if success_rate_by_method is not None
            else {}
        ),
        success_rate_by_failure_code=(
            success_rate_by_failure_code
            if success_rate_by_failure_code is not None
            else {}
        ),
        success_rate_by_strategy=(
            success_rate_by_strategy
            if success_rate_by_strategy is not None
            else {}
        ),
    )


def get_categories(
    *,
    insights_report,
) -> list[str]:
    """
    Return insight categories for simpler
    assertions.
    """

    return [
        insight.category
        for insight
        in insights_report.insights
    ]


def get_insight(
    *,
    insights_report,
    category: str,
):
    """
    Return one insight for a category.
    """

    for insight in insights_report.insights:

        if insight.category == category:
            return insight

    return None


# ============================================================
# EMPTY REPORT
# ============================================================


def test_empty_report_produces_no_insights():

    report = create_report()

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert insights_report.insights == []


# ============================================================
# RECOVERY PERFORMANCE
# ============================================================


def test_low_recovery_rate_creates_insight():

    report = create_report(
        total_payments=100,
        recovery_rate=20.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "recovery_performance"
        in get_categories(
            insights_report=insights_report,
        )
    )


def test_recovery_rate_at_threshold_does_not_create_insight():

    report = create_report(
        total_payments=100,
        recovery_rate=30.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "recovery_performance"
        not in get_categories(
            insights_report=insights_report,
        )
    )


def test_good_recovery_rate_does_not_create_insight():

    report = create_report(
        total_payments=100,
        recovery_rate=75.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "recovery_performance"
        not in get_categories(
            insights_report=insights_report,
        )
    )


# ============================================================
# FAILURE RATE
# ============================================================


def test_high_failure_rate_creates_insight():

    report = create_report(
        total_payments=100,
        failure_rate=40.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "recovery_failures"
        in get_categories(
            insights_report=insights_report,
        )
    )


def test_failure_rate_below_threshold_does_not_create_insight():

    report = create_report(
        total_payments=100,
        failure_rate=20.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "recovery_failures"
        not in get_categories(
            insights_report=insights_report,
        )
    )


# ============================================================
# APPROVAL RATE
# ============================================================


def test_high_approval_rate_creates_insight():

    report = create_report(
        total_payments=100,
        approval_rate=70.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "human_approval"
        in get_categories(
            insights_report=insights_report,
        )
    )


def test_low_approval_rate_does_not_create_insight():

    report = create_report(
        total_payments=100,
        approval_rate=20.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "human_approval"
        not in get_categories(
            insights_report=insights_report,
        )
    )


# ============================================================
# ESCALATION RATE
# ============================================================


def test_high_escalation_rate_creates_insight():

    report = create_report(
        total_payments=100,
        escalation_rate=80.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "escalation"
        in get_categories(
            insights_report=insights_report,
        )
    )


def test_low_escalation_rate_does_not_create_insight():

    report = create_report(
        total_payments=100,
        escalation_rate=20.0,
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "escalation"
        not in get_categories(
            insights_report=insights_report,
        )
    )


# ============================================================
# PAYMENT METHOD PERFORMANCE
# ============================================================


def test_best_payment_method_creates_insight():

    report = create_report(
        total_payments=100,
        success_rate_by_method={
            "card": 40.0,
            "upi": 80.0,
            "netbanking": 60.0,
        },
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    insight = get_insight(
        insights_report=insights_report,
        category="payment_method_performance",
    )

    assert insight is not None

    assert "upi" in insight.message

    assert "80.00%" in insight.message


def test_best_payment_method_uses_highest_rate():

    report = create_report(
        total_payments=10,
        success_rate_by_method={
            "card": 90.0,
            "upi": 50.0,
        },
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    insight = get_insight(
        insights_report=insights_report,
        category="payment_method_performance",
    )

    assert insight is not None

    assert "card" in insight.message

    assert "90.00%" in insight.message


def test_no_payment_method_insight_without_method_data():

    report = create_report(
        total_payments=100,
        success_rate_by_method={},
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    assert (
        "payment_method_performance"
        not in get_categories(
            insights_report=insights_report,
        )
    )


# ============================================================
# COMBINED INSIGHTS
# ============================================================


def test_multiple_insights_can_be_generated():

    report = create_report(
        total_payments=100,
        recovery_rate=20.0,
        failure_rate=40.0,
        approval_rate=70.0,
        escalation_rate=80.0,
        success_rate_by_method={
            "card": 30.0,
            "upi": 90.0,
        },
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    categories = get_categories(
        insights_report=insights_report,
    )

    assert (
        "recovery_performance"
        in categories
    )

    assert (
        "recovery_failures"
        in categories
    )

    assert (
        "human_approval"
        in categories
    )

    assert (
        "escalation"
        in categories
    )

    assert (
        "payment_method_performance"
        in categories
    )


def test_insight_categories_are_unique():

    report = create_report(
        total_payments=100,
        recovery_rate=20.0,
        failure_rate=40.0,
        approval_rate=70.0,
        escalation_rate=80.0,
        success_rate_by_method={
            "card": 30.0,
            "upi": 90.0,
        },
    )

    insights_report = (
        RecoveryInsights().analyze(
            report=report,
        )
    )

    categories = get_categories(
        insights_report=insights_report,
    )

    assert len(categories) == len(
        set(categories)
    )