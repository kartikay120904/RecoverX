from decimal import Decimal
from random import Random

from backend.app.domain.enums import (
    PaymentFailureCode,
)

from simulator.analytics.recovery_reporter import (
    RecoveryAnalyticsReporter,
)

from simulator.data.payment_generator import (
    PaymentBatchGenerator,
)

from simulator.recovery.batch_runner import (
    BatchRecoveryRunner,
)


def create_report(
    *,
    count: int = 20,
):
    """
    Create a deterministic analytics report
    for testing.
    """

    payments = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=count,
        )
    )

    batch_result = (
        BatchRecoveryRunner(
            rng=Random(42),
        ).run(
            payments,
        )
    )

    report = (
        RecoveryAnalyticsReporter().build(
            payments=payments,
            batch_result=batch_result,
        )
    )

    return (
        payments,
        batch_result,
        report,
    )


def test_report_matches_batch_metrics():

    (
        _,
        batch_result,
        report,
    ) = create_report()

    assert (
        report.total_payments
        == batch_result.total_payments
    )

    assert (
        report.total_failed_payments
        == batch_result.total_failed_payments
    )

    assert (
        report.total_recovery_proposals
        == batch_result.total_recovery_proposals
    )

    assert (
        report.successful_recoveries
        == batch_result.total_recovered
    )

    assert (
        report.failed_recoveries
        == batch_result.total_failed_recoveries
    )


def test_report_revenue_metrics():

    (
        _,
        batch_result,
        report,
    ) = create_report()

    assert (
        report.revenue_at_risk
        == batch_result.total_revenue_at_risk
    )

    assert (
        report.recovered_revenue
        == batch_result.total_recovered_revenue
    )

    assert (
        report.unrecovered_revenue
        == max(
            Decimal("0"),
            report.revenue_at_risk
            - report.recovered_revenue,
        )
    )


def test_report_failure_breakdown():

    (
        payments,
        _,
        report,
    ) = create_report(
        count=50,
    )

    expected_total = sum(
        1
        for payment in payments
        if payment.failure_code is not None
    )

    actual_total = sum(
        report.failure_code_breakdown.values()
    )

    assert (
        actual_total
        == expected_total
    )


def test_report_contains_failure_categories():

    (
        _,
        _,
        report,
    ) = create_report(
        count=50,
    )

    assert len(
        report.failure_code_breakdown
    ) > 0


def test_report_strategy_breakdown_matches_attempts():

    (
        _,
        batch_result,
        report,
    ) = create_report()

    assert (
        sum(
            report.strategy_breakdown.values()
        )
        == len(
            batch_result.attempts
        )
    )


def test_success_and_failure_strategy_totals():

    (
        _,
        _,
        report,
    ) = create_report()

    successful_total = sum(
        report.successful_strategy_breakdown.values()
    )

    failed_total = sum(
        report.failed_strategy_breakdown.values()
    )

    assert (
        successful_total
        == report.successful_recoveries
    )

    assert (
        failed_total
        == report.failed_recoveries
    )


def test_report_recovery_rate_matches_batch():

    (
        _,
        batch_result,
        report,
    ) = create_report()

    assert (
        report.recovery_rate
        == batch_result.recovery_rate
    )


def test_report_is_deterministic():

    (
        _,
        _,
        first,
    ) = create_report(
        count=30,
    )

    (
        _,
        _,
        second,
    ) = create_report(
        count=30,
    )

    assert (
        first.total_payments
        == second.total_payments
    )

    assert (
        first.recovery_rate
        == second.recovery_rate
    )

    assert (
        first.revenue_at_risk
        == second.revenue_at_risk
    )

    assert (
        first.recovered_revenue
        == second.recovered_revenue
    )

    assert (
        first.failure_code_breakdown
        == second.failure_code_breakdown
    )

    assert (
        first.strategy_breakdown
        == second.strategy_breakdown
    )