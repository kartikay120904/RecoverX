from decimal import Decimal

from backend.app.domain.enums import RecoveryStrategy
from simulator.analytics.incident_analysis import analyze_incident
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


def test_incident_analysis_returns_result():
    result = create_result()

    analysis = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    assert analysis is not None
    assert isinstance(analysis.detected, bool)
    assert analysis.severity in {
        "normal",
        "medium",
        "high",
        "critical",
    }


def test_detected_incident_has_failed_payments():
    result = create_result()

    analysis = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    if analysis.detected:
        assert analysis.affected_payments > 0
        assert analysis.affected_volume > Decimal("0")


def test_no_incident_returns_no_action():
    result = create_result()

    analysis = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=1.0,
        failure_code_threshold=1.0,
    )

    assert analysis.detected is False
    assert analysis.severity == "normal"
    assert analysis.affected_payments == 0
    assert analysis.affected_volume == Decimal("0")
    assert analysis.affected_methods == []
    assert analysis.affected_merchants == []
    assert analysis.dominant_failure_codes == []
    assert analysis.recommended_strategy == RecoveryStrategy.NO_ACTION


def test_detected_incident_has_valid_recovery_strategy():
    result = create_result()

    analysis = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    if analysis.detected:
        assert analysis.recommended_strategy in {
            RecoveryStrategy.SEND_REMINDER,
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStrategy.ESCALATE,
        }


def test_incident_analysis_is_deterministic():
    result_one = create_result()
    result_two = create_result()

    analysis_one = analyze_incident(
        result_one.payments,
        result_one.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    analysis_two = analyze_incident(
        result_two.payments,
        result_two.orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.20,
    )

    assert analysis_one == analysis_two