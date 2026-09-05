from random import Random

from simulator.simulation.batch_runner import (
    BatchRecoveryRunner,
)
from simulator.simulation.payment_factory import (
    SyntheticPaymentFactory,
)


def test_batch_runner_processes_all_payments():

    rng = Random(42)

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=rng,
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(42),
        )
    )

    assert (
        result.total_payments
        == 20
    )


def test_batch_runner_creates_recovery_proposals():

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=Random(10),
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(10),
        )
    )

    assert (
        result.proposals_created
        > 0
    )


def test_batch_runner_executes_proposals():

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=Random(20),
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(20),
        )
    )

    assert (
        result.executions_completed
        == (
            result.successful_recoveries
            + result.failed_recoveries
        )
    )


def test_batch_runner_is_deterministic():

    factory = (
        SyntheticPaymentFactory()
    )

    first_payments = (
        factory.create_batch(
            size=30,
            rng=Random(99),
        )
    )

    second_payments = (
        factory.create_batch(
            size=30,
            rng=Random(99),
        )
    )

    first = (
        BatchRecoveryRunner().run(
            payments=first_payments,
            rng=Random(99),
        )
    )

    second = (
        BatchRecoveryRunner().run(
            payments=second_payments,
            rng=Random(99),
        )
    )

    assert (
        first.total_payments
        == second.total_payments
    )

    assert (
        first.proposals_created
        == second.proposals_created
    )

    assert (
        first.successful_recoveries
        == second.successful_recoveries
    )

    assert (
        first.failed_recoveries
        == second.failed_recoveries
    )