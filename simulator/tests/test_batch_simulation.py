from random import Random

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
)

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.simulation import (
    BatchSimulation,
    BatchSimulationConfig,
)


def test_zero_payment_simulation():

    coordinator = (
        RecoveryEscalationCoordinator()
    )

    simulation = BatchSimulation(
        coordinator=coordinator,
    )

    result = simulation.run(
        BatchSimulationConfig(
            payment_count=0,
            seed=42,
        )
    )

    assert (
        result.metrics.total_payments
        == 0
    )

    assert result.results == []


def test_negative_payment_count_raises():

    coordinator = (
        RecoveryEscalationCoordinator()
    )

    simulation = BatchSimulation(
        coordinator=coordinator,
    )

    try:

        simulation.run(
            BatchSimulationConfig(
                payment_count=-1,
            )
        )

        assert False

    except ValueError as error:

        assert (
            str(error)
            == "payment_count cannot be negative."
        )


def test_simulation_processes_requested_payments():

    coordinator = (
        RecoveryEscalationCoordinator()
    )

    simulation = BatchSimulation(
        coordinator=coordinator,
    )

    result = simulation.run(
        BatchSimulationConfig(
            payment_count=10,
            seed=42,
        )
    )

    assert (
        result.metrics.total_payments
        == 10
    )

    assert (
        len(result.results)
        == 10
    )