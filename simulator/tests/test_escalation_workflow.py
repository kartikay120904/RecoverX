from decimal import Decimal

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.audit.service import AuditService
from simulator.recovery.escalation import (
    EscalationService,
)
from simulator.recovery.escalation_policy import (
    EscalationPolicy,
)
from simulator.recovery.escalation_workflow import (
    EscalationWorkflow,
)


def create_payment() -> Payment:
    return Payment(
        amount=Decimal("1000.00"),
        method=PaymentMethod.CARD,
        status=PaymentStatus.FAILED,
        failure_code="payment_declined",
    )


def create_attempt(
    payment: Payment,
    probability: float = 0.90,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        payment_id=payment.payment_id,
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        predicted_probability=probability,
        predicted_revenue=(
            payment.amount
            * Decimal(str(probability))
        ),
    )


def create_workflow() -> EscalationWorkflow:

    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service=audit_service
    )

    escalation_policy = EscalationPolicy()

    return EscalationWorkflow(
        policy=escalation_policy,
        service=escalation_service,
    )


def test_workflow_does_not_escalate_safe_recovery():

    workflow = create_workflow()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.90,
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
    )

    assert (
        result.decision.should_escalate
        is False
    )

    assert result.escalation is None


def test_workflow_escalates_low_confidence():

    workflow = create_workflow()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.30,
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.payment_id
        == payment.payment_id
    )

    assert (
        result.escalation.reason
        == "recovery confidence too low"
    )


def test_workflow_escalates_when_human_approval_required():

    workflow = create_workflow()

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
        requires_human_approval=True,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.reason
        == "recovery requires human approval"
    )


def test_workflow_escalates_when_retry_limit_reached():

    workflow = create_workflow()

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
        retry_limit_reached=True,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.reason
        == "retry limit exceeded"
    )


def test_workflow_escalates_high_value_payment():

    workflow = create_workflow()

    payment = Payment(
        amount=Decimal("100000.00"),
        method=PaymentMethod.CARD,
        status=PaymentStatus.FAILED,
        failure_code="payment_declined",
    )

    attempt = create_attempt(
        payment
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
        high_value_threshold=50000,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.reason
        == "high-value payment requires review"
    )


def test_workflow_escalates_when_no_recovery_action_exists():

    workflow = create_workflow()

    payment = create_payment()

    result = workflow.evaluate(
        payment=payment,
        attempt=None,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.reason
        == "no recovery action available"
    )


def test_workflow_escalates_repeated_execution_failures():

    workflow = create_workflow()

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    result = workflow.evaluate(
        payment=payment,
        attempt=attempt,
        execution_failures=2,
        max_execution_failures=2,
    )

    assert (
        result.decision.should_escalate
        is True
    )

    assert result.escalation is not None

    assert (
        result.escalation.reason
        == (
            "recovery execution "
            "repeatedly failed"
        )
    )