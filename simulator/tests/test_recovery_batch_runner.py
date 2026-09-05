from decimal import Decimal
from random import Random
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
)

from simulator.recovery.batch_runner import (
    BatchRecoveryRunner,
)


def make_payment(
    *,
    amount: str = "1000",
    failure_code: str,
) -> Payment:
    """
    Create a failed payment for batch recovery tests.
    """

    return Payment(
        payment_id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal(amount),
        currency="INR",
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=failure_code,
    )


def test_batch_runner_processes_payments():
    """
    The batch runner should create and execute
    a recovery workflow for every recoverable
    failed payment.
    """

    payments = [
        make_payment(
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.AUTHENTICATION_FAILED.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    assert result.total_payments == 3

    assert (
        result.total_failed_payments
        == 3
    )

    assert (
        result.total_recovery_proposals
        == 3
    )

    assert len(
        result.attempts
    ) == 3


def test_batch_runner_calculates_revenue_at_risk():
    """
    Revenue at risk should equal the total value
    of failed payments in the batch.
    """

    payments = [
        make_payment(
            amount="1000",
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            amount="2000",
            failure_code=(
                PaymentFailureCode.NETWORK_ERROR.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    assert (
        result.total_payments
        == 2
    )

    assert (
        result.total_failed_payments
        == 2
    )

    assert (
        result.total_revenue_at_risk
        == Decimal("3000")
    )

    assert (
        result.total_recovered_revenue
        >= Decimal("0")
    )


def test_batch_runner_records_terminal_results():
    """
    Every executed recovery attempt should end
    in a terminal status.
    """

    payments = [
        make_payment(
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.AUTHENTICATION_FAILED.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    terminal_statuses = {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
    }

    assert all(
        attempt.status
        in terminal_statuses
        for attempt in result.attempts
    )


def test_batch_runner_metrics_match_attempt_results():
    """
    Aggregated batch metrics should match
    the terminal recovery attempts.
    """

    payments = [
        make_payment(
            amount="1000",
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            amount="2000",
            failure_code=(
                PaymentFailureCode.NETWORK_ERROR.value
            ),
        ),
        make_payment(
            amount="3000",
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    successful_attempts = [
        attempt
        for attempt in result.attempts
        if (
            attempt.status
            == RecoveryStatus.SUCCEEDED
        )
    ]

    failed_attempts = [
        attempt
        for attempt in result.attempts
        if (
            attempt.status
            == RecoveryStatus.FAILED
        )
    ]

    assert (
        result.total_recovered
        == len(successful_attempts)
    )

    assert (
        result.total_failed_recoveries
        == len(failed_attempts)
    )

    assert (
        result.total_recovered
        + result.total_failed_recoveries
        == result.total_recovery_proposals
    )


def test_batch_runner_calculates_recovery_rate():
    """
    Recovery rate should equal successful
    recoveries divided by recovery proposals.
    """

    payments = [
        make_payment(
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.NETWORK_ERROR.value
            ),
        ),
        make_payment(
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    expected_rate = (
        result.total_recovered
        / result.total_recovery_proposals
    )

    assert (
        result.recovery_rate
        == round(
            expected_rate,
            4,
        )
    )


def test_batch_runner_recovered_revenue_matches_successes():
    """
    Recovered revenue should equal the sum of
    actual revenue from successful recoveries.
    """

    payments = [
        make_payment(
            amount="1000",
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            amount="2500",
            failure_code=(
                PaymentFailureCode.AUTHENTICATION_FAILED.value
            ),
        ),
        make_payment(
            amount="5000",
            failure_code=(
                PaymentFailureCode.NETWORK_ERROR.value
            ),
        ),
    ]

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        payments,
    )

    expected_recovered_revenue = sum(
        (
            attempt.actual_revenue
            or Decimal("0")
        )
        for attempt in result.attempts
        if (
            attempt.status
            == RecoveryStatus.SUCCEEDED
        )
    )

    assert (
        result.total_recovered_revenue
        == expected_recovered_revenue
    )


def test_batch_runner_is_deterministic():
    """
    The same random seed should produce
    identical batch recovery metrics.
    """

    payments_one = [
        make_payment(
            amount="1000",
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            amount="2000",
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
        make_payment(
            amount="3000",
            failure_code=(
                PaymentFailureCode.AUTHENTICATION_FAILED.value
            ),
        ),
    ]

    payments_two = [
        make_payment(
            amount="1000",
            failure_code=(
                PaymentFailureCode.BANK_TIMEOUT.value
            ),
        ),
        make_payment(
            amount="2000",
            failure_code=(
                PaymentFailureCode.INSUFFICIENT_FUNDS.value
            ),
        ),
        make_payment(
            amount="3000",
            failure_code=(
                PaymentFailureCode.AUTHENTICATION_FAILED.value
            ),
        ),
    ]

    result_one = (
        BatchRecoveryRunner(
            rng=Random(42),
        ).run(
            payments_one,
        )
    )

    result_two = (
        BatchRecoveryRunner(
            rng=Random(42),
        ).run(
            payments_two,
        )
    )

    assert (
        result_one.total_payments
        == result_two.total_payments
    )

    assert (
        result_one.total_failed_payments
        == result_two.total_failed_payments
    )

    assert (
        result_one.total_recovery_proposals
        == result_two.total_recovery_proposals
    )

    assert (
        result_one.total_recovered
        == result_two.total_recovered
    )

    assert (
        result_one.total_failed_recoveries
        == result_two.total_failed_recoveries
    )

    assert (
        result_one.total_recovered_revenue
        == result_two.total_recovered_revenue
    )

    assert (
        result_one.recovery_rate
        == result_two.recovery_rate
    )


def test_batch_runner_handles_empty_batch():
    """
    An empty batch should return valid
    zero-value recovery metrics.
    """

    runner = BatchRecoveryRunner(
        rng=Random(42),
    )

    result = runner.run(
        [],
    )

    assert (
        result.total_payments
        == 0
    )

    assert (
        result.total_failed_payments
        == 0
    )

    assert (
        result.total_recovery_proposals
        == 0
    )

    assert (
        result.total_recovered
        == 0
    )

    assert (
        result.total_failed_recoveries
        == 0
    )

    assert (
        result.total_revenue_at_risk
        == Decimal("0")
    )

    assert (
        result.total_recovered_revenue
        == Decimal("0")
    )

    assert (
        result.recovery_rate
        == 0.0
    )

    assert result.attempts == ()