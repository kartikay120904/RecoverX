import pytest

from simulator.batch.recovery_batch_simulation import (
    RecoveryBatchSimulation,
)


def test_simulation_runs_requested_number_of_payments():

    simulation = (
        RecoveryBatchSimulation()
    )

    result = simulation.run(
        count=5,
        seed=42,
    )

    assert len(
        result.payments
    ) == 5

    assert (
        result.batch_result.metrics.total_payments
        == 5
    )

    assert len(
        result.batch_result.results
    ) == 5


def test_zero_payment_simulation():

    simulation = (
        RecoveryBatchSimulation()
    )

    result = simulation.run(
        count=0,
        seed=42,
    )

    assert result.payments == []

    assert (
        result.batch_result.results
        == []
    )

    assert (
        result.batch_result.metrics.total_payments
        == 0
    )


def test_negative_count_raises_error():

    simulation = (
        RecoveryBatchSimulation()
    )

    with pytest.raises(
        ValueError,
        match="Simulation count cannot be negative",
    ):

        simulation.run(
            count=-1,
            seed=42,
        )


def test_same_seed_produces_same_payment_snapshot():

    first_simulation = (
        RecoveryBatchSimulation()
    )

    second_simulation = (
        RecoveryBatchSimulation()
    )

    first_result = (
        first_simulation.run(
            count=5,
            seed=42,
        )
    )

    second_result = (
        second_simulation.run(
            count=5,
            seed=42,
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


def test_metrics_match_generated_payments():

    simulation = (
        RecoveryBatchSimulation()
    )

    result = simulation.run(
        count=10,
        seed=42,
    )

    metrics = (
        result.batch_result.metrics
    )

    assert (
        metrics.total_payments
        == len(result.payments)
    )

    assert (
        len(
            result.batch_result.results
        )
        == len(result.payments)
    )