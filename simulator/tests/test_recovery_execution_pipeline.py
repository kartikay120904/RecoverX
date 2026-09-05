from decimal import Decimal
from random import Random

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
)

from backend.app.domain.models import (
    Payment,
)

from simulator.recovery.recovery_execution_pipeline import (
    RecoveryExecutionPipeline,
)


def create_failed_payment() -> Payment:
    return Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )


def test_pipeline_proposes_and_executes_recovery():

    payment = create_failed_payment()

    result = (
        RecoveryExecutionPipeline().run(
            payment=payment,
            rng=Random(1),
        )
    )

    assert result.payment == payment

    assert result.attempt is not None

    assert (
        result.attempt.status
        == RecoveryStatus.SUCCEEDED
    )


def test_pipeline_returns_none_for_non_recoverable_payment():

    payment = create_failed_payment()

    payment.status = (
        PaymentStatus.CAPTURED
    )

    result = (
        RecoveryExecutionPipeline().run(
            payment=payment,
            rng=Random(1),
        )
    )

    assert result.attempt is None


def test_pipeline_execution_is_deterministic():

    first_payment = (
        create_failed_payment()
    )

    second_payment = (
        create_failed_payment()
    )

    pipeline = (
        RecoveryExecutionPipeline()
    )

    first_result = pipeline.run(
        payment=first_payment,
        rng=Random(42),
    )

    second_result = pipeline.run(
        payment=second_payment,
        rng=Random(42),
    )

    assert (
        first_result.attempt
        is not None
    )

    assert (
        second_result.attempt
        is not None
    )

    assert (
        first_result.attempt.status
        == second_result.attempt.status
    )

    assert (
        first_result.attempt.actual_revenue
        == second_result.attempt.actual_revenue
    )