from simulator.analytics.anomaly_detection import (
    detect_anomalies,
    detect_failure_code_anomalies,
    detect_method_anomalies,
    detect_merchant_anomalies,
    detect_overall_failure_rate_anomaly,
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


def test_overall_failure_rate_anomaly_requires_minimum_sample():
    result = create_result()

    anomaly = detect_overall_failure_rate_anomaly(
        result.payments[:10],
        threshold=0.20,
    )

    assert anomaly is None


def test_overall_failure_rate_anomaly_detected():
    result = create_result()

    anomaly = detect_overall_failure_rate_anomaly(
        result.payments,
        threshold=0.05,
    )

    assert anomaly is not None
    assert anomaly.metric == "failure_rate"
    assert anomaly.dimension == "overall"
    assert anomaly.value >= anomaly.threshold
    assert anomaly.severity in {
        "medium",
        "high",
        "critical",
    }


def test_method_anomalies_return_valid_results():
    result = create_result()

    anomalies = detect_method_anomalies(
        result.payments,
        threshold=0.05,
    )

    for anomaly in anomalies:
        assert anomaly.metric == "failure_rate"
        assert anomaly.dimension.startswith("method:")
        assert anomaly.value >= anomaly.threshold
        assert anomaly.severity in {
            "medium",
            "high",
            "critical",
        }


def test_merchant_anomalies_return_valid_results():
    result = create_result()

    anomalies = detect_merchant_anomalies(
        result.payments,
        result.orders,
        threshold=0.05,
    )

    for anomaly in anomalies:
        assert anomaly.metric == "failure_rate"
        assert anomaly.dimension.startswith("merchant:")
        assert anomaly.value >= anomaly.threshold


def test_failure_code_anomalies_return_valid_results():
    result = create_result()

    anomalies = detect_failure_code_anomalies(
        result.payments,
        threshold=0.20,
    )

    for anomaly in anomalies:
        assert anomaly.metric == "failure_code_concentration"
        assert anomaly.dimension.startswith("failure_code:")
        assert anomaly.value >= anomaly.threshold


def test_detect_anomalies_combines_detectors():
    result = create_result()

    anomalies = detect_anomalies(
        result.payments,
        result.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    assert isinstance(anomalies, list)

    for anomaly in anomalies:
        assert anomaly.value >= anomaly.threshold
        assert anomaly.severity in {
            "medium",
            "high",
            "critical",
        }