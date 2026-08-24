from simulator.recovery.engine import RecoveryEngine
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)


def create_failed_payment():
    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=4,
            customers_per_merchant=10,
            orders_per_customer=5,
        )
    )

    return next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    )


def test_recovery_engine_proposes_for_failed_payment():
    payment = create_failed_payment()

    engine = RecoveryEngine()
    attempt = engine.propose(payment)

    assert attempt is not None
    assert attempt.payment_id == payment.payment_id
    assert attempt.status == RecoveryStatus.PROPOSED
    assert 0 <= attempt.predicted_probability <= 1
    assert attempt.predicted_revenue >= 0


def test_recovery_engine_ignores_successful_payment():
    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=4,
            customers_per_merchant=10,
            orders_per_customer=5,
        )
    )

    payment = next(
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.CAPTURED
    )

    engine = RecoveryEngine()

    assert engine.propose(payment) is None


def test_timeout_uses_retry_strategy():
    payment = create_failed_payment()
    payment.failure_code = PaymentFailureCode.BANK_TIMEOUT.value

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RETRY_PAYMENT


def test_insufficient_funds_uses_reminder():
    payment = create_failed_payment()
    payment.failure_code = PaymentFailureCode.INSUFFICIENT_FUNDS.value

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.SEND_REMINDER


def test_authentication_failure_uses_recovery_link():
    payment = create_failed_payment()
    payment.failure_code = PaymentFailureCode.AUTHENTICATION_FAILED.value

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RECOVERY_LINK