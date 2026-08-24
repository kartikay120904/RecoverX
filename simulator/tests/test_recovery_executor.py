from random import Random

import pytest

from backend.app.domain.enums import (
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)

from simulator.recovery.engine import RecoveryEngine
from simulator.recovery.executor import RecoveryExecutor
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


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


def test_successful_recovery_records_revenue():
    payment = create_failed_payment()

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None

    attempt.predicted_probability = 1.0

    result = RecoveryExecutor().execute(
        attempt,
        payment,
        Random(42),
    )

    assert result.status == RecoveryStatus.SUCCEEDED
    assert result.actual_revenue == payment.amount


def test_failed_recovery_records_zero_revenue():
    payment = create_failed_payment()

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None

    attempt.predicted_probability = 0.0

    result = RecoveryExecutor().execute(
        attempt,
        payment,
        Random(42),
    )

    assert result.status == RecoveryStatus.FAILED
    assert result.actual_revenue == 0


def test_only_proposed_attempt_can_be_executed():
    payment = create_failed_payment()

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None

    attempt.status = RecoveryStatus.SUCCEEDED

    with pytest.raises(ValueError):
        RecoveryExecutor().execute(
            attempt,
            payment,
            Random(42),
        )


def test_recovery_execution_preserves_payment_id():
    payment = create_failed_payment()

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None

    result = RecoveryExecutor().execute(
        attempt,
        payment,
        Random(42),
    )

    assert result.payment_id == payment.payment_id