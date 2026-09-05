from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment
from simulator.recovery.engine import RecoveryEngine


def make_failed_payment(failure_code: str) -> Payment:
    return Payment(
        payment_id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("1000"),
        currency="INR",
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=failure_code,
    )


def test_bank_timeout_recommends_retry():
    payment = make_failed_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RETRY_PAYMENT
    assert attempt.predicted_probability == 0.70
    assert attempt.predicted_revenue == Decimal("700.0")
    assert attempt.status == RecoveryStatus.PROPOSED


def test_network_error_recommends_retry():
    payment = make_failed_payment(
        PaymentFailureCode.NETWORK_ERROR.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RETRY_PAYMENT


def test_gateway_timeout_recommends_retry():
    payment = make_failed_payment(
        PaymentFailureCode.GATEWAY_TIMEOUT.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RETRY_PAYMENT


def test_insufficient_funds_recommends_reminder():
    payment = make_failed_payment(
        PaymentFailureCode.INSUFFICIENT_FUNDS.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.SEND_REMINDER
    assert attempt.predicted_probability == 0.45
    assert attempt.predicted_revenue == Decimal("450.00")


def test_authentication_failure_recommends_recovery_link():
    payment = make_failed_payment(
        PaymentFailureCode.AUTHENTICATION_FAILED.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RECOVERY_LINK


def test_payment_declined_recommends_recovery_link():
    payment = make_failed_payment(
        PaymentFailureCode.PAYMENT_DECLINED.value
    )

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.RECOVERY_LINK


def test_successful_payment_is_not_recoverable():
    payment = make_failed_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    payment.status = PaymentStatus.CAPTURED

    attempt = RecoveryEngine().propose(payment)

    assert attempt is None

def test_non_failed_payment_is_not_recoverable():
    payment = make_failed_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    payment.status = PaymentStatus.CAPTURED

    engine = RecoveryEngine()

    assert engine.is_recoverable(payment) is False


def test_payment_without_failure_code_is_not_recoverable():
    payment = make_failed_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    payment.failure_code = None

    attempt = RecoveryEngine().propose(payment)

    assert attempt is None

def test_excessive_retry_attempts_escalate():
    payment = make_failed_payment(
        PaymentFailureCode.BANK_TIMEOUT.value
    )

    payment.attempt_number = 4

    attempt = RecoveryEngine().propose(payment)

    assert attempt is not None
    assert attempt.strategy == RecoveryStrategy.ESCALATE
    assert attempt.status == RecoveryStatus.PROPOSED

    