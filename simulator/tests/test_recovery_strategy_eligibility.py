from decimal import Decimal

import pytest

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment
from backend.app.services.recovery_strategy_eligibility import (
    RecoveryStrategyEligibilityService,
)


@pytest.fixture
def service():
    return RecoveryStrategyEligibilityService()


def create_payment(
    *,
    status=PaymentStatus.FAILED,
    failure_code=None,
):
    return Payment(
        amount=Decimal("1000.00"),
        method=PaymentMethod.UPI,
        status=status,
        failure_code=failure_code,
    )


@pytest.mark.parametrize(
    "failure_code",
    [
        PaymentFailureCode.BANK_TIMEOUT,
        PaymentFailureCode.GATEWAY_TIMEOUT,
        PaymentFailureCode.NETWORK_ERROR,
    ],
)
def test_transient_failure_allows_retry(
    service,
    failure_code,
):
    payment = create_payment(
        failure_code=failure_code,
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert (
        RecoveryStrategy.RETRY_PAYMENT
        in strategies
    )

    assert (
        RecoveryStrategy.RECOVERY_LINK
        in strategies
    )

    assert (
        RecoveryStrategy.ESCALATE
        in strategies
    )


def test_insufficient_funds_prefers_delayed_recovery(
    service,
):
    payment = create_payment(
        failure_code=(
            PaymentFailureCode.INSUFFICIENT_FUNDS
        ),
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert (
        RecoveryStrategy.SEND_REMINDER
        in strategies
    )

    assert (
        RecoveryStrategy.RECOVERY_LINK
        in strategies
    )

    assert (
        RecoveryStrategy.RETRY_PAYMENT
        not in strategies
    )


def test_authentication_failure_allows_recovery_link(
    service,
):
    payment = create_payment(
        failure_code=(
            PaymentFailureCode.AUTHENTICATION_FAILED
        ),
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert (
        strategies
        == [
            RecoveryStrategy.RECOVERY_LINK,
            RecoveryStrategy.ESCALATE,
        ]
    )


def test_payment_declined_allows_alternative_recovery(
    service,
):
    payment = create_payment(
        failure_code=(
            PaymentFailureCode.PAYMENT_DECLINED
        ),
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert (
        RecoveryStrategy.RECOVERY_LINK
        in strategies
    )

    assert (
        RecoveryStrategy.SEND_REMINDER
        in strategies
    )


def test_unknown_failure_returns_general_strategies(
    service,
):
    payment = create_payment(
        failure_code="unknown_failure",
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert strategies == [
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStrategy.SEND_REMINDER,
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStrategy.ESCALATE,
    ]


def test_none_failure_code_returns_general_strategies(
    service,
):
    payment = create_payment(
        failure_code=None,
    )

    strategies = service.eligible_strategies(
        payment,
    )

    assert len(strategies) == 4


@pytest.mark.parametrize(
    "status",
    [
        PaymentStatus.CREATED,
        PaymentStatus.AUTHORIZED,
        PaymentStatus.CAPTURED,
        PaymentStatus.SUCCEEDED,
        PaymentStatus.REFUNDED,
        PaymentStatus.RETRYING,
    ],
)
def test_non_failed_payment_has_no_recovery_strategies(
    service,
    status,
):
    payment = create_payment(
        status=status,
    )

    assert (
        service.eligible_strategies(
            payment,
        )
        == []
    )


def test_retry_eligible_payment_can_be_recovered(
    service,
):
    payment = create_payment(
        status=PaymentStatus.RETRY_ELIGIBLE,
        failure_code=(
            PaymentFailureCode.NETWORK_ERROR
        ),
    )

    assert (
        service.is_strategy_eligible(
            payment,
            RecoveryStrategy.RETRY_PAYMENT,
        )
        is True
    )


def test_strategy_eligibility_returns_false_for_invalid_strategy(
    service,
):
    payment = create_payment(
        failure_code=(
            PaymentFailureCode.AUTHENTICATION_FAILED
        ),
    )

    assert (
        service.is_strategy_eligible(
            payment,
            RecoveryStrategy.RETRY_PAYMENT,
        )
        is False
    )


def test_no_action_is_never_eligible(
    service,
):
    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
    )

    assert (
        service.is_strategy_eligible(
            payment,
            RecoveryStrategy.NO_ACTION,
        )
        is False
    )