from backend.app.domain.enums import (
    PaymentStatus,
    RecoveryStatus,
)

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


def test_failed_payments_have_recovery_attempts():
    result = create_result()

    failed_payments = [
        payment
        for payment in result.payments
        if payment.status == PaymentStatus.FAILED
    ]

    assert len(result.recovery_attempts) == len(failed_payments)


def test_recovery_attempts_reference_existing_payments():
    result = create_result()

    payment_ids = {
        payment.payment_id
        for payment in result.payments
    }

    for attempt in result.recovery_attempts:
        assert attempt.payment_id in payment_ids


def test_recovery_attempts_have_terminal_status():
    result = create_result()

    for attempt in result.recovery_attempts:
        assert attempt.status in {
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        }


def test_recovery_simulation_is_deterministic():
    config = SimulationRunConfig(
        seed=42,
        merchant_count=4,
        customers_per_merchant=10,
        orders_per_customer=5,
    )

    first = run_simulation(config)
    second = run_simulation(config)

    assert first.recovery_attempts == second.recovery_attempts