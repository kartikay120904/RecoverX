from decimal import Decimal
from random import Random

from simulator.analytics.metrics import (
    RecoveryMetricsCalculator,
)
from simulator.simulation.batch_runner import (
    BatchRecoveryRunner,
)
from simulator.simulation.payment_factory import (
    SyntheticPaymentFactory,
)


def test_metrics_calculates_batch_totals():

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=Random(42),
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(42),
        )
    )

    metrics = (
        RecoveryMetricsCalculator().calculate(
            result
        )
    )

    assert (
        metrics.total_payments
        == 20
    )

    assert (
        metrics.proposals_created
        == result.proposals_created
    )

    assert (
        metrics.executions_completed
        == result.executions_completed
    )


def test_metrics_actual_revenue_is_non_negative():

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

    metrics = (
        RecoveryMetricsCalculator().calculate(
            result
        )
    )

    assert (
        metrics.actual_recovered_revenue
        >= Decimal("0")
    )


def test_metrics_success_rate_is_valid():

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=Random(99),
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(99),
        )
    )

    metrics = (
        RecoveryMetricsCalculator().calculate(
            result
        )
    )

    assert (
        Decimal("0")
        <= metrics.recovery_success_rate
        <= Decimal("100")
    )


def test_metrics_proposal_rate_is_valid():

    payments = (
        SyntheticPaymentFactory().create_batch(
            size=20,
            rng=Random(55),
        )
    )

    result = (
        BatchRecoveryRunner().run(
            payments=payments,
            rng=Random(55),
        )
    )

    metrics = (
        RecoveryMetricsCalculator().calculate(
            result
        )
    )

    assert (
        Decimal("0")
        <= metrics.proposal_rate
        <= Decimal("100")
    )


def test_empty_batch_produces_zero_rates():

    result = (
        BatchRecoveryRunner().run(
            payments=[],
            rng=Random(1),
        )
    )

    metrics = (
        RecoveryMetricsCalculator().calculate(
            result
        )
    )

    assert (
        metrics.recovery_success_rate
        == Decimal("0")
    )

    assert (
        metrics.proposal_rate
        == Decimal("0")
    )