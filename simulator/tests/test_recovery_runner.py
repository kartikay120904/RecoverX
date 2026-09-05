from backend.app.domain.enums import (
    PaymentStatus,
    RecoveryStatus,
)
from simulator.recovery.runner import (
    RecoverySimulationRunner,
)


def test_generated_payment_is_failed():
    runner = RecoverySimulationRunner(
        seed=42
    )

    payment = runner.generate_payment()

    assert payment.status == PaymentStatus.FAILED


def test_generated_payment_has_failure_code():
    runner = RecoverySimulationRunner(
        seed=42
    )

    payment = runner.generate_payment()

    assert payment.failure_code is not None


def test_run_returns_requested_attempts():
    runner = RecoverySimulationRunner(
        seed=42
    )

    attempts = runner.run(10)

    assert len(attempts) == 10


def test_completed_attempts_have_terminal_status():
    runner = RecoverySimulationRunner(
        seed=42
    )

    attempts = runner.run(20)

    terminal_statuses = {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
    }

    assert all(
        attempt.status in terminal_statuses
        for attempt in attempts
    )


def test_zero_simulation():
    runner = RecoverySimulationRunner(
        seed=42
    )

    attempts = runner.run(0)

    assert attempts == []


def test_negative_count_raises_error():
    runner = RecoverySimulationRunner(
        seed=42
    )

    try:
        runner.run(-1)

        assert False, (
            "Expected ValueError for negative count."
        )

    except ValueError as error:
        assert (
            str(error)
            == "Simulation count cannot be negative."
        )


def test_simulation_is_repeatable_in_structure():
    first_runner = RecoverySimulationRunner(
        seed=100
    )

    second_runner = RecoverySimulationRunner(
        seed=100
    )

    first_attempts = first_runner.run(10)

    second_attempts = second_runner.run(10)

    assert len(first_attempts) == len(
        second_attempts
    )

    first_structure = [
        (
            attempt.strategy,
            attempt.status,
            attempt.predicted_probability,
            attempt.predicted_revenue,
            attempt.actual_revenue,
        )
        for attempt in first_attempts
    ]

    second_structure = [
        (
            attempt.strategy,
            attempt.status,
            attempt.predicted_probability,
            attempt.predicted_revenue,
            attempt.actual_revenue,
        )
        for attempt in second_attempts
    ]

    assert first_structure == second_structure