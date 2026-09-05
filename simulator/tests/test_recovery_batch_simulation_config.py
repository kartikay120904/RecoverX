from simulator.batch.recovery_batch_simulation import (
    RecoveryBatchSimulation,
)

from simulator.batch.recovery_simulation_config import (
    RecoverySimulationConfig,
)


def test_simulation_runs_with_config():

    simulation = (
        RecoveryBatchSimulation()
    )

    config = (
        RecoverySimulationConfig(
            count=5,
            seed=42,
            scenario_name="baseline",
        )
    )

    result = simulation.run_config(
        config=config,
    )

    assert len(
        result.payments
    ) == 5

    assert (
        result.batch_result.metrics.total_payments
        == 5
    )


def test_same_config_produces_same_payment_snapshot():

    config = (
        RecoverySimulationConfig(
            count=10,
            seed=42,
            scenario_name="deterministic-test",
        )
    )

    first_simulation = (
        RecoveryBatchSimulation()
    )

    second_simulation = (
        RecoveryBatchSimulation()
    )

    first_result = (
        first_simulation.run_config(
            config=config,
        )
    )

    second_result = (
        second_simulation.run_config(
            config=config,
        )
    )

    first_snapshot = [
        (
            payment.payment_id,
            payment.amount,
            payment.method,
            payment.failure_code,
        )
        for payment in (
            first_result.payments
        )
    ]

    second_snapshot = [
        (
            payment.payment_id,
            payment.amount,
            payment.method,
            payment.failure_code,
        )
        for payment in (
            second_result.payments
        )
    ]

    assert (
        first_snapshot
        == second_snapshot
    )