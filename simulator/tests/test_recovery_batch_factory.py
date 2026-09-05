from random import Random

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.recovery_batch_factory import (
    RecoveryBatchFactory,
)


def test_factory_creates_working_batch_runner():

    runner = (
        RecoveryBatchFactory.create()
    )

    assert runner is not None


def test_factory_runs_batch():

    generator = PaymentGenerator()

    payments = generator.generate(
        count=5,
        rng=Random(42),
    )

    runner = (
        RecoveryBatchFactory.create()
    )

    result = runner.run(
        payments=payments,
        rng=Random(42),
    )

    assert result.metrics.total_payments == 5

    assert len(result.results) == 5