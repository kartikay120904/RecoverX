from decimal import Decimal

from backend.app.domain.enums import (
    PaymentMethod,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.audit.service import (
    AuditService,
)
from simulator.recovery.escalation import (
    EscalationService,
    EscalationStatus,
)
from simulator.recovery.escalation_manager import (
    EscalationManager,
)
from simulator.recovery.escalation_policy import (
    EscalationPolicy,
)


def create_manager():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    policy = EscalationPolicy()

    manager = EscalationManager(
        policy=policy,
        service=escalation_service,
    )

    return (
        manager,
        escalation_service,
        audit_service,
    )


def create_payment(
    amount: str = "1000",
) -> Payment:

    return Payment(
        amount=Decimal(amount),
        method=PaymentMethod.UPI,
    )


def create_attempt(
    payment: Payment,
    probability: float = 0.8,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        payment_id=payment.payment_id,
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        predicted_probability=probability,
        predicted_revenue=(
            payment.amount
            * Decimal(
                str(probability)
            )
        ),
    )


def test_no_escalation_when_policy_allows():

    (
        manager,
        escalation_service,
        _,
    ) = create_manager()

    payment = create_payment()

    result = manager.evaluate(
        payment=payment,
        confidence=0.9,
        high_value_threshold=50_000,
    )

    assert (
        result.decision.should_escalate
        is False
    )

    assert (
        result.escalation
        is None
    )

    assert (
        escalation_service.open_escalations()
        == []
    )


def test_low_confidence_creates_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.3,
    )

    result = manager.evaluate(
        payment=payment,
        attempt=attempt,
        confidence=0.3,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )

    assert (
        result.escalation.status
        == EscalationStatus.OPEN
    )

    assert (
        result.escalation.payment_id
        == payment.payment_id
    )


def test_human_approval_creates_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    result = manager.evaluate(
        payment=payment,
        requires_human_approval=True,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )

    assert (
        result.escalation.reason
        == "recovery requires human approval"
    )


def test_retry_limit_creates_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    result = manager.evaluate(
        payment=payment,
        retry_limit_reached=True,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )

    assert (
        result.escalation.reason
        == "retry limit exceeded"
    )


def test_high_value_payment_creates_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment(
        amount="100000"
    )

    result = manager.evaluate(
        payment=payment,
        high_value_threshold=50_000,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )


def test_execution_failures_create_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    result = manager.evaluate(
        payment=payment,
        execution_failures=2,
        max_execution_failures=2,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )


def test_missing_recovery_action_creates_escalation():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    result = manager.evaluate(
        payment=payment,
        has_recovery_action=False,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert (
        result.escalation
        is not None
    )


def test_escalation_links_recovery_attempt():

    (
        manager,
        _,
        _,
    ) = create_manager()

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    result = manager.evaluate(
        payment=payment,
        attempt=attempt,
        requires_human_approval=True,
    )

    assert (
        result.escalation
        is not None
    )

    assert (
        result.escalation.recovery_id
        == attempt.recovery_id
    )