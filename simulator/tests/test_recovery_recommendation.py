from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentStatus,
    RecoveryStrategy,
)
from simulator.analytics.incident_analysis import IncidentAnalysis
from simulator.analytics.recovery_recommendation import (
    recommend_recoveries,
    recommend_recovery,
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


def create_incident():
    return IncidentAnalysis(
        detected=True,
        severity="high",
        affected_payments=20,
        affected_volume=Decimal("20000"),
        affected_methods=["upi"],
        affected_merchants=[],
        dominant_failure_codes=[
            PaymentFailureCode.BANK_TIMEOUT.value,
        ],
        recommended_strategy=RecoveryStrategy.RETRY_PAYMENT,
    )


def test_recommendation_is_created():
    result = create_result()
    incident = create_incident()

    failed_payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )

    recommendation = recommend_recovery(
        failed_payment,
        incident,
    )

    assert recommendation.payment_id == str(
        failed_payment.payment_id
    )

    assert recommendation.strategy in {
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStrategy.SEND_REMINDER,
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION,
    }

    assert 0 <= recommendation.predicted_probability <= 1
    assert recommendation.predicted_revenue >= Decimal("0")
    assert recommendation.reason


def test_timeout_failure_recommends_retry():
    result = create_result()
    incident = create_incident()

    payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )

    payment.failure_code = PaymentFailureCode.BANK_TIMEOUT.value

    recommendation = recommend_recovery(
        payment,
        incident,
    )

    assert recommendation.strategy == RecoveryStrategy.RETRY_PAYMENT


def test_insufficient_funds_recommends_reminder():
    result = create_result()
    incident = create_incident()

    payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )

    payment.failure_code = (
        PaymentFailureCode.INSUFFICIENT_FUNDS.value
    )

    recommendation = recommend_recovery(
        payment,
        incident,
    )

    assert recommendation.strategy == RecoveryStrategy.SEND_REMINDER


def test_declined_payment_recommends_recovery_link():
    result = create_result()
    incident = create_incident()

    payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )

    payment.failure_code = (
        PaymentFailureCode.PAYMENT_DECLINED.value
    )

    recommendation = recommend_recovery(
        payment,
        incident,
    )

    assert recommendation.strategy == RecoveryStrategy.RECOVERY_LINK


def test_recommend_recoveries_returns_failed_payments_only():
    result = create_result()
    incident = create_incident()

    recommendations = recommend_recoveries(
        result.payments,
        incident,
    )

    expected_count = sum(
        payment.status == PaymentStatus.FAILED
        for payment in result.payments
    )

    assert len(recommendations) == expected_count


def test_recommendation_is_deterministic():
    result = create_result()
    incident = create_incident()

    payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )

    first = recommend_recovery(
        payment,
        incident,
    )

    second = recommend_recovery(
        payment,
        incident,
    )

    assert first == second