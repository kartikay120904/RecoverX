import pytest

from simulator.simulation.recovery_simulation_service import (
    RecoverySimulationService,
)


def test_runs_empty_simulation():
    service = (
        RecoverySimulationService()
    )

    result = service.run(
        count=0,
        seed=42,
    )

    assert result.metrics.total_payments == 0

    assert result.results == []


def test_runs_requested_number_of_payments():
    service = (
        RecoverySimulationService()
    )

    result = service.run(
        count=5,
        seed=42,
    )

    assert result.metrics.total_payments == 5

    assert len(
        result.results
    ) == 5


def test_negative_count_raises_error():
    service = (
        RecoverySimulationService()
    )

    with pytest.raises(
        ValueError,
        match=(
            "count must be greater than "
            "or equal to zero"
        ),
    ):

        service.run(
            count=-1,
            seed=42,
        )


def test_same_seed_produces_same_metrics():
    first_service = (
        RecoverySimulationService()
    )

    second_service = (
        RecoverySimulationService()
    )

    first_result = (
        first_service.run(
            count=10,
            seed=42,
        )
    )

    second_result = (
        second_service.run(
            count=10,
            seed=42,
        )
    )

    assert (
        first_result.metrics
        == second_result.metrics
    )


def test_different_seed_runs_successfully():
    service = (
        RecoverySimulationService()
    )

    first_result = (
        service.run(
            count=10,
            seed=42,
        )
    )

    second_result = (
        service.run(
            count=10,
            seed=99,
        )
    )

    assert (
        first_result.metrics.total_payments
        == 10
    )

    assert (
        second_result.metrics.total_payments
        == 10
    )