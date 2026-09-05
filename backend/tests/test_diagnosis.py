from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment

from simulator.recovery.diagnosis import (
    PaymentFailureDiagnoser,
)


def create_payment(
    failure_code: PaymentFailureCode | None,
) -> Payment:

    return Payment(
        order_id="11111111-1111-1111-1111-111111111111",
        customer_id="22222222-2222-2222-2222-222222222222",
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code=(
            failure_code.value
            if failure_code
            else None
        ),
    )


def test_bank_timeout_recommends_retry():

    diagnoser = PaymentFailureDiagnoser()

    payment = create_payment(
        PaymentFailureCode.BANK_TIMEOUT
    )

    diagnosis = diagnoser.diagnose(
        payment
    )

    assert (
        diagnosis.category
        == "temporary_bank_failure"
    )

    assert (
        diagnosis.recommended_strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_insufficient_funds_recommends_reminder():

    diagnoser = PaymentFailureDiagnoser()

    payment = create_payment(
        PaymentFailureCode.INSUFFICIENT_FUNDS
    )

    diagnosis = diagnoser.diagnose(
        payment
    )

    assert (
        diagnosis.recommended_strategy
        == RecoveryStrategy.SEND_REMINDER
    )


def test_authentication_failure_recommends_recovery_link():

    diagnoser = PaymentFailureDiagnoser()

    payment = create_payment(
        PaymentFailureCode.AUTHENTICATION_FAILED
    )

    diagnosis = diagnoser.diagnose(
        payment
    )

    assert (
        diagnosis.recommended_strategy
        == RecoveryStrategy.RECOVERY_LINK
    )


def test_unknown_failure_escalates():

    diagnoser = PaymentFailureDiagnoser()

    payment = create_payment(
        None
    )

    diagnosis = diagnoser.diagnose(
        payment
    )

    assert (
        diagnosis.recommended_strategy
        == RecoveryStrategy.NO_ACTION
    )