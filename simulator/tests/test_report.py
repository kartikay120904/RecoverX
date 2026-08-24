from decimal import Decimal

from simulator.analytics.report import build_simulation_report
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


def create_result():
    return run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=4,
            customers_per_merchant=10,
            orders_per_customer=5,
        )
    )


def test_report_is_created():
    result = create_result()

    report = build_simulation_report(
        payments=result.payments,
        orders=result.orders,
        customers=result.customers,
        merchants=result.merchants,
    )

    assert report.payment_metrics.total_payments == len(
        result.payments
    )

    assert report.payment_metrics.total_volume > Decimal("0")


def test_report_contains_anomaly_analysis():
    result = create_result()

    report = build_simulation_report(
        payments=result.payments,
        orders=result.orders,
        customers=result.customers,
        merchants=result.merchants,
    )

    assert isinstance(report.anomalies, list)
    assert report.incident is not None


def test_report_contains_recovery_recommendations():
    result = create_result()

    report = build_simulation_report(
        payments=result.payments,
        orders=result.orders,
        customers=result.customers,
        merchants=result.merchants,
    )

    failed_payments = [
        payment
        for payment in result.payments
        if payment.failure_code is not None
    ]

    assert (
        report.total_recovery_recommendations
        == len(failed_payments)
    )

    assert report.predicted_recovery_revenue >= Decimal("0")


def test_report_is_deterministic():
    first_result = create_result()
    second_result = create_result()

    first_report = build_simulation_report(
        payments=first_result.payments,
        orders=first_result.orders,
        customers=first_result.customers,
        merchants=first_result.merchants,
    )

    second_report = build_simulation_report(
        payments=second_result.payments,
        orders=second_result.orders,
        customers=second_result.customers,
        merchants=second_result.merchants,
    )

    assert first_report.payment_metrics == second_report.payment_metrics
    assert first_report.success_rate_by_method == second_report.success_rate_by_method
    assert first_report.failure_code_distribution == second_report.failure_code_distribution
    assert first_report.anomalies == second_report.anomalies
    assert first_report.incident == second_report.incident
    assert (
        first_report.recovery_recommendations
        == second_report.recovery_recommendations
    )