from simulator.batch.recovery_batch_reporter import (
    RecoveryBatchReporter,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)

from simulator.batch.recovery_metrics import (
    RecoveryMetrics,
)


def create_result(
    metrics: RecoveryMetrics,
) -> RecoveryBatchResult:
    """
    Create a minimal batch result for
    reporter testing.
    """

    return RecoveryBatchResult(
        results=[],
        metrics=metrics,
    )


def test_render_report():
    metrics = RecoveryMetrics(
        total_payments=100,
        payments_flagged=70,
        recovery_attempts=60,
        successful_recoveries=30,
        failed_recoveries=20,
        blocked_recoveries=10,
        approval_required=5,
        escalations=8,
        revenue_recovered=50000.0,
    )

    result = create_result(
        metrics
    )

    reporter = RecoveryBatchReporter()

    report = reporter.render(
        result
    )

    assert (
        "RECOVERX — REVENUE RECOVERY BATCH REPORT"
        in report
    )

    assert (
        "Total Payments Processed: 100"
        in report
    )

    assert (
        "Payments Flagged: 70"
        in report
    )

    assert (
        "Recovery Attempts: 60"
        in report
    )

    assert (
        "Successful Recoveries: 30"
        in report
    )

    assert (
        "Failed Recoveries: 20"
        in report
    )

    assert (
        "Blocked Recoveries: 10"
        in report
    )

    assert (
        "Approval Required: 5"
        in report
    )

    assert (
        "Escalations: 8"
        in report
    )

    assert (
        "Revenue Recovered: ₹50,000.00"
        in report
    )

    assert (
        "Recovery Rate: 50.00%"
        in report
    )


def test_render_empty_batch():
    metrics = RecoveryMetrics()

    result = create_result(
        metrics
    )

    reporter = RecoveryBatchReporter()

    report = reporter.render(
        result
    )

    assert (
        "Total Payments Processed: 0"
        in report
    )

    assert (
        "Recovery Attempts: 0"
        in report
    )

    assert (
        "Revenue Recovered: ₹0.00"
        in report
    )

    assert (
        "Recovery Rate: 0.00%"
        in report
    )