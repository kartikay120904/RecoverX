from simulator.batch.recovery_batch_simulation import (
    RecoveryBatchSimulation,
)

from simulator.batch.recovery_scenario_factory import (
    RecoveryScenarioFactory,
)


def test_baseline_scenario_runs():

    simulation = (
        RecoveryBatchSimulation()
    )

    config = (
        RecoveryScenarioFactory.baseline(
            count=10,
            seed=42,
        )
    )

    result = (
        simulation.run_config(
            config=config,
        )
    )

    assert (
        result.batch_result.metrics.total_payments
        == 10
    )


def test_high_value_scenario_runs_without_changing_core_logic():

    simulation = (
        RecoveryBatchSimulation()
    )

    config = (
        RecoveryScenarioFactory.high_value(
            count=10,
            seed=42,
        )
    )

    result = (
        simulation.run_config(
            config=config,
        )
    )

    assert (
        result.batch_result.metrics.total_payments
        == 10
    )


def test_same_scenario_and_seed_is_deterministic():

    config = (
        RecoveryScenarioFactory.baseline(
            count=10,
            seed=42,
        )
    )

    first = (
        RecoveryBatchSimulation()
        .run_config(
            config=config,
        )
    )

    second = (
        RecoveryBatchSimulation()
        .run_config(
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
        for payment in first.payments
    ]

    second_snapshot = [
        (
            payment.payment_id,
            payment.amount,
            payment.method,
            payment.failure_code,
        )
        for payment in second.payments
    ]

    assert (
        first_snapshot
        == second_snapshot
    )