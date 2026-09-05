
from simulator.batch.recovery_metrics import (
    RecoveryMetrics,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)

from simulator.simulation.recovery_simulation_report import (
    RecoverySimulationReport,
)


def test_report_copies_metrics():
    metrics = RecoveryMetrics(
        total_payments=10,
        payments_flagged=8,
        recovery_attempts=8,
        successful_recoveries=5,
        failed_recoveries=2,
        blocked_recoveries=1,
        approval_required=2,
        escalations=3,
        revenue_recovered=5000.0,
    )

    batch_result = (
        RecoveryBatchResult(
            results=[],
            metrics=metrics,
        )
    )

    report = (
        RecoverySimulationReport.from_batch_result(
            batch_result
        )
    )

    assert report.total_payments == 10

    assert report.payments_flagged == 8

    assert report.recovery_attempts == 8

    assert report.successful_recoveries == 5

    assert report.failed_recoveries == 2

    assert report.blocked_recoveries == 1

    assert report.approval_required == 2

    assert report.escalations == 3

    assert report.revenue_recovered == 5000.0

    assert report.recovery_rate == 62.5


def test_unsuccessful_recoveries():
    report = RecoverySimulationReport(
        total_payments=10,
        payments_flagged=10,
        recovery_attempts=10,
        successful_recoveries=6,
        failed_recoveries=3,
        blocked_recoveries=1,
        approval_required=0,
        escalations=0,
        revenue_recovered=6000.0,
        recovery_rate=60.0,
    )

    assert (
        report.unsuccessful_recoveries
        == 4
    )


def test_average_revenue_per_success():
    report = RecoverySimulationReport(
        total_payments=10,
        payments_flagged=10,
        recovery_attempts=10,
        successful_recoveries=5,
        failed_recoveries=5,
        blocked_recoveries=0,
        approval_required=0,
        escalations=0,
        revenue_recovered=5000.0,
        recovery_rate=50.0,
    )

    assert (
        report.average_revenue_per_success
        == 1000.0
    )


def test_average_revenue_is_zero_without_success():
    report = RecoverySimulationReport(
        total_payments=10,
        payments_flagged=5,
        recovery_attempts=5,
        successful_recoveries=0,
        failed_recoveries=5,
        blocked_recoveries=0,
        approval_required=0,
        escalations=0,
        revenue_recovered=0.0,
        recovery_rate=0.0,
    )

    assert (
        report.average_revenue_per_success
        == 0.0
    )


def test_payment_flag_rate():
    report = RecoverySimulationReport(
        total_payments=10,
        payments_flagged=7,
        recovery_attempts=7,
        successful_recoveries=3,
        failed_recoveries=4,
        blocked_recoveries=0,
        approval_required=0,
        escalations=0,
        revenue_recovered=3000.0,
        recovery_rate=(
            3 / 7
        ) * 100,
    )

    assert (
        report.payment_flag_rate
        == 70.0
    )


def test_escalation_rate():
    report = RecoverySimulationReport(
        total_payments=20,
        payments_flagged=15,
        recovery_attempts=15,
        successful_recoveries=10,
        failed_recoveries=5,
        blocked_recoveries=0,
        approval_required=2,
        escalations=5,
        revenue_recovered=10000.0,
        recovery_rate=(
            10 / 15
        ) * 100,
    )

    assert (
        report.escalation_rate
        == 25.0
    )


def test_rates_are_zero_for_empty_report():
    report = RecoverySimulationReport(
        total_payments=0,
        payments_flagged=0,
        recovery_attempts=0,
        successful_recoveries=0,
        failed_recoveries=0,
        blocked_recoveries=0,
        approval_required=0,
        escalations=0,
        revenue_recovered=0.0,
        recovery_rate=0.0,
    )

    assert (
        report.payment_flag_rate
        == 0.0
    )

    assert (
        report.escalation_rate
        == 0.0
    )