from random import Random

from backend.app.domain.enums import (
    RecoveryStatus,
)

from simulator.analytics.recovery_analytics import (
    RecoveryAnalytics,
)

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
)

from simulator.batch.recovery_metrics import (
    RecoveryMetrics,
)


class StubResult:
    """
    Minimal result object used to test analytics
    independently from the recovery implementation.
    """

    def __init__(
        self,
        *,
        attempt=None,
        executed=False,
        blocked=False,
        requires_approval=False,
    ) -> None:

        class Orchestration:
            pass

        self.orchestration = Orchestration()

        self.orchestration.attempt = attempt
        self.orchestration.executed = executed
        self.orchestration.blocked = blocked
        self.orchestration.requires_approval = (
            requires_approval
        )


class StubAttempt:
    """
    Minimal recovery attempt used for analytics tests.
    """

    def __init__(
        self,
        *,
        payment_id,
        status,
        actual_revenue=0.0,
        strategy="retry",
    ) -> None:

        self.payment_id = payment_id

        self.status = status

        self.actual_revenue = actual_revenue

        self.strategy = strategy


def create_batch_result(
    *,
    results,
    metrics,
) -> RecoveryBatchResult:
    """
    Create a RecoveryBatchResult for analytics tests.
    """

    return RecoveryBatchResult(
        results=results,
        metrics=metrics,
    )


def get_method_value(
    payment,
) -> str:
    """
    Return the normalized payment method value.

    Supports both:

    - plain strings
    - enum values
    """

    return getattr(
        payment.method,
        "value",
        str(payment.method),
    )


def test_empty_batch_analytics():
    """
    Analytics should safely handle an empty batch.
    """

    batch_result = create_batch_result(
        results=[],
        metrics=RecoveryMetrics(),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.total_payments == 0
    assert report.recovery_rate == 0.0
    assert report.failure_rate == 0.0
    assert report.approval_rate == 0.0
    assert report.escalation_rate == 0.0
    assert report.revenue_recovered == 0.0
    assert report.average_recovered_revenue == 0.0
    assert report.success_rate_by_method == {}


def test_recovery_rates():
    """
    Recovery and failure rates should be calculated
    from recovery attempts.
    """

    metrics = RecoveryMetrics(
        total_payments=10,
        recovery_attempts=10,
        successful_recoveries=4,
        failed_recoveries=3,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.total_payments == 10
    assert report.recovery_rate == 40.0
    assert report.failure_rate == 30.0


def test_recovery_rate_with_no_attempts():
    """
    Recovery analytics should not divide by zero when
    no recovery attempts were made.
    """

    metrics = RecoveryMetrics(
        total_payments=10,
        recovery_attempts=0,
        successful_recoveries=0,
        failed_recoveries=0,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.recovery_rate == 0.0
    assert report.failure_rate == 0.0


def test_approval_rate():
    """
    Approval rate should be calculated against the
    total number of processed payments.
    """

    metrics = RecoveryMetrics(
        total_payments=10,
        approval_required=4,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.approval_rate == 40.0


def test_approval_rate_with_empty_batch():
    """
    Approval rate should safely handle zero payments.
    """

    batch_result = create_batch_result(
        results=[],
        metrics=RecoveryMetrics(
            total_payments=0,
            approval_required=0,
        ),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.approval_rate == 0.0


def test_escalation_rate():
    """
    Escalation rate should be calculated against the
    total number of processed payments.
    """

    metrics = RecoveryMetrics(
        total_payments=20,
        escalations=5,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.escalation_rate == 25.0


def test_escalation_rate_with_empty_batch():
    """
    Escalation rate should safely handle zero payments.
    """

    batch_result = create_batch_result(
        results=[],
        metrics=RecoveryMetrics(
            total_payments=0,
            escalations=0,
        ),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.escalation_rate == 0.0


def test_average_recovered_revenue():
    """
    Average recovered revenue should be calculated
    using successful recoveries.
    """

    metrics = RecoveryMetrics(
        successful_recoveries=4,
        revenue_recovered=1000.0,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.revenue_recovered == 1000.0
    assert report.average_recovered_revenue == 250.0


def test_average_recovered_revenue_without_successes():
    """
    Average recovered revenue should be zero when
    there are no successful recoveries.
    """

    metrics = RecoveryMetrics(
        successful_recoveries=0,
        revenue_recovered=0.0,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.average_recovered_revenue == 0.0


def test_success_rate_by_payment_method():
    """
    Success rates should be correctly grouped by
    payment method.

    This test supports deterministic generated
    payments without assuming that both payments
    have the same method.
    """

    generator = PaymentGenerator()

    payments = generator.generate(
        count=2,
        rng=Random(42),
    )

    first_attempt = StubAttempt(
        payment_id=payments[0].payment_id,
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=500.0,
    )

    second_attempt = StubAttempt(
        payment_id=payments[1].payment_id,
        status=RecoveryStatus.FAILED,
    )

    results = [
        StubResult(
            attempt=first_attempt,
            executed=True,
        ),
        StubResult(
            attempt=second_attempt,
            executed=True,
        ),
    ]

    metrics = RecoveryMetrics(
        total_payments=2,
        payments_flagged=2,
        recovery_attempts=2,
        successful_recoveries=1,
        failed_recoveries=1,
        revenue_recovered=500.0,
    )

    batch_result = create_batch_result(
        results=results,
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
        payments=payments,
    )

    first_method = get_method_value(
        payments[0]
    )

    second_method = get_method_value(
        payments[1]
    )

    if first_method == second_method:

        assert (
            report.success_rate_by_method[
                first_method
            ]
            == 50.0
        )

        assert len(
            report.success_rate_by_method
        ) == 1

    else:

        assert (
            report.success_rate_by_method[
                first_method
            ]
            == 100.0
        )

        assert (
            report.success_rate_by_method[
                second_method
            ]
            == 0.0
        )

        assert len(
            report.success_rate_by_method
        ) == 2


def test_success_rate_by_method_without_payments():
    """
    Method-level analytics should return an empty
    result when payment data is not provided.
    """

    batch_result = create_batch_result(
        results=[],
        metrics=RecoveryMetrics(
            total_payments=2,
            recovery_attempts=2,
        ),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert report.success_rate_by_method == {}


def test_attempt_with_unknown_payment_is_ignored():
    """
    Recovery attempts whose payment cannot be found
    should not create invalid method analytics.
    """

    generator = PaymentGenerator()

    payments = generator.generate(
        count=1,
        rng=Random(42),
    )

    unknown_payment_id = (
        PaymentGenerator().generate(
            count=2,
            rng=Random(99),
        )[1].payment_id
    )

    attempt = StubAttempt(
        payment_id=unknown_payment_id,
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=500.0,
    )

    results = [
        StubResult(
            attempt=attempt,
            executed=True,
        )
    ]

    batch_result = create_batch_result(
        results=results,
        metrics=RecoveryMetrics(
            total_payments=1,
            recovery_attempts=1,
            successful_recoveries=1,
            revenue_recovered=500.0,
        ),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
        payments=payments,
    )

    assert report.success_rate_by_method == {}


def test_result_without_attempt_is_ignored():
    """
    Results without recovery attempts should not
    affect method-level recovery analytics.
    """

    generator = PaymentGenerator()

    payments = generator.generate(
        count=1,
        rng=Random(42),
    )

    results = [
        StubResult(
            attempt=None,
            blocked=True,
        )
    ]

    batch_result = create_batch_result(
        results=results,
        metrics=RecoveryMetrics(
            total_payments=1,
            blocked_recoveries=1,
        ),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
        payments=payments,
    )

    assert report.success_rate_by_method == {}

def test_failure_code_analytics_without_payments():

    metrics = RecoveryMetrics(
        total_payments=1,
    )

    batch_result = create_batch_result(
        results=[],
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert (
        report.success_rate_by_failure_code
        == {}
    )

def test_success_rate_by_failure_code():

    generator = PaymentGenerator()

    payments = generator.generate(
        count=2,
        rng=Random(42),
    )

    first_attempt = StubAttempt(
        payment_id=payments[0].payment_id,
        status=RecoveryStatus.SUCCEEDED,
        actual_revenue=500.0,
    )

    second_attempt = StubAttempt(
        payment_id=payments[1].payment_id,
        status=RecoveryStatus.FAILED,
    )

    results = [
        StubResult(
            attempt=first_attempt,
            executed=True,
        ),
        StubResult(
            attempt=second_attempt,
            executed=True,
        ),
    ]

    metrics = RecoveryMetrics(
        total_payments=2,
        payments_flagged=2,
        recovery_attempts=2,
        successful_recoveries=1,
        failed_recoveries=1,
        revenue_recovered=500.0,
    )

    batch_result = create_batch_result(
        results=results,
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
        payments=payments,
    )

    first_failure_code = str(
        payments[0].failure_code
    )

    second_failure_code = str(
        payments[1].failure_code
    )

    if (
        first_failure_code
        == second_failure_code
    ):

        assert (
            report.success_rate_by_failure_code[
                first_failure_code
            ]
            == 50.0
        )

    else:

        assert (
            report.success_rate_by_failure_code[
                first_failure_code
            ]
            == 100.0
        )

        assert (
            report.success_rate_by_failure_code[
                second_failure_code
            ]
            == 0.0
        )


def test_strategy_analytics_with_no_attempts():

    batch_result = create_batch_result(
        results=[],
        metrics=RecoveryMetrics(),
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert (
        report.success_rate_by_strategy
        == {}
    )

def test_success_rate_by_strategy():

    first_attempt = StubAttempt(
        payment_id="payment_1",
        status=RecoveryStatus.SUCCEEDED,
        strategy="retry",
    )

    second_attempt = StubAttempt(
        payment_id="payment_2",
        status=RecoveryStatus.FAILED,
        strategy="retry",
    )

    third_attempt = StubAttempt(
        payment_id="payment_3",
        status=RecoveryStatus.SUCCEEDED,
        strategy="alternate_method",
    )

    results = [
        StubResult(
            attempt=first_attempt,
            executed=True,
        ),
        StubResult(
            attempt=second_attempt,
            executed=True,
        ),
        StubResult(
            attempt=third_attempt,
            executed=True,
        ),
    ]

    metrics = RecoveryMetrics(
        total_payments=3,
        recovery_attempts=3,
        successful_recoveries=2,
        failed_recoveries=1,
    )

    batch_result = create_batch_result(
        results=results,
        metrics=metrics,
    )

    report = RecoveryAnalytics().analyze(
        batch_result=batch_result,
    )

    assert (
        report.success_rate_by_strategy[
            "retry"
        ]
        == 50.0
    )

    assert (
        report.success_rate_by_strategy[
            "alternate_method"
        ]
        == 100.0
    )