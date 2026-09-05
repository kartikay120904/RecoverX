from decimal import Decimal
from random import Random

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
)
from backend.app.domain.models import Payment

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrator,
)


def test_low_confidence_recovery_requires_escalation():

    payment = Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        failure_code=(
            PaymentFailureCode.INSUFFICIENT_FUNDS
        ),
    )

    orchestrator = (
        RecoveryOrchestrator()
    )

    result = orchestrator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.requires_approval
        is True
    )

    assert (
        result.escalation_required
        is True
    )

    assert (
        result.executed
        is False
    )


def test_high_value_recovery_requires_escalation():

    payment = Payment(
        amount=Decimal("100000"),
        method=PaymentMethod.UPI,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
    )

    orchestrator = (
        RecoveryOrchestrator()
    )

    result = orchestrator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.requires_approval
        is True
    )

    assert (
        result.escalation_required
        is True
    )

    assert (
        result.executed
        is False
    )


def test_safe_recovery_does_not_require_escalation():

    payment = Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
    )

    orchestrator = (
        RecoveryOrchestrator()
    )

    result = orchestrator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.requires_approval
        is False
    )

    assert (
        result.escalation_required
        is False
    )


def test_orchestrator_result_remains_compatible():

    payment = Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
    )

    orchestrator = (
        RecoveryOrchestrator()
    )

    result = orchestrator.recover(
        payment=payment,
        rng=Random(1),
    )

    assert result.attempt is not None

    assert result.policy_decision is not None

    assert isinstance(
        result.escalation_required,
        bool,
    )