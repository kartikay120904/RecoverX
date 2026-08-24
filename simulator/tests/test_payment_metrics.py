from decimal import Decimal

from simulator.analytics.payment_metrics import (
    calculate_payment_metrics,
    failure_code_distribution,
    failure_rate_by_customer_segment,
    failure_rate_by_merchant,
    success_rate_by_method,
)
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


def create_result():
    config = SimulationRunConfig(
        seed=42,
        merchant_count=4,
        customers_per_merchant=10,
        orders_per_customer=5,
    )

    return run_simulation(config)


def test_payment_metrics_calculates_totals():
    result = create_result()

    metrics = calculate_payment_metrics(result.payments)

    assert metrics.total_payments == len(result.payments)

    assert (
        metrics.successful_payments
        + metrics.failed_payments
        == metrics.total_payments
    )

    assert (
        metrics.successful_volume
        + metrics.failed_volume
        == metrics.total_volume
    )

    assert metrics.total_volume > Decimal("0")

    assert 0 <= metrics.success_rate <= 1
    assert 0 <= metrics.failure_rate <= 1


def test_success_rate_by_method_is_valid():
    result = create_result()

    rates = success_rate_by_method(result.payments)

    assert rates

    for rate in rates.values():
        assert 0 <= rate <= 1


def test_failure_code_distribution_matches_failed_payments():
    result = create_result()

    distribution = failure_code_distribution(result.payments)

    total_failures = sum(distribution.values())

    expected_failures = sum(
        payment.status.value == "failed"
        for payment in result.payments
    )

    assert total_failures == expected_failures


def test_failure_rate_by_merchant_is_valid():
    result = create_result()

    rates = failure_rate_by_merchant(
        result.payments,
        result.orders,
    )

    assert len(rates) == len(result.merchants)

    for rate in rates.values():
        assert 0 <= rate <= 1


def test_failure_rate_by_customer_segment_is_valid():
    result = create_result()

    rates = failure_rate_by_customer_segment(
        result.payments,
        result.customers,
    )

    assert rates

    for rate in rates.values():
        assert 0 <= rate <= 1