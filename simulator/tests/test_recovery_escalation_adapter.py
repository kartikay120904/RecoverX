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

from backend.app.recovery.escalation_adapter import (
    RecoveryEscalationAdapter,
)

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrationResult,
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


def create_adapter() -> RecoveryEscalationAdapter:

    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service=audit_service
    )

    escalation_policy = EscalationPolicy()

    workflow = EscalationWorkflow(
        policy=escalation_policy,
        service=escalation_service,
    )

    return RecoveryEscalationAdapter(
        escalation_workflow=workflow
    )


def test_successful_orchestration_does_not_escalate():

    adapter = create_adapter()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.90,
    )

    orchestration = (
        RecoveryOrchestrationResult(
            attempt=attempt,
            policy_decision=None,
            executed=True,
            blocked=False,
            requires_approval=False,
            reason=(
                "Recovery workflow completed."
            ),
        )
    )

    result = adapter.evaluate(
        payment=payment,
        orchestration=orchestration,
    )

    assert result.escalation is None


def test_human_approval_orchestration_escalates():

    adapter = create_adapter()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.90,
    )

    orchestration = (
        RecoveryOrchestrationResult(
            attempt=attempt,
            policy_decision=None,
            executed=False,
            blocked=False,
            requires_approval=True,
            reason=(
                "Recovery requires human approval."
            ),
        )
    )

    result = adapter.evaluate(
        payment=payment,
        orchestration=orchestration,
    )

    assert result.escalation is not None

    assert (
        result.escalation.decision.should_escalate
        is True
    )

    assert (
        result.escalation.escalation
        is not None
    )


def test_retry_limit_orchestration_escalates():

    adapter = create_adapter()

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    orchestration = (
        RecoveryOrchestrationResult(
            attempt=attempt,
            policy_decision=None,
            executed=False,
            blocked=True,
            requires_approval=False,
            reason=(
                "Retry limit reached. "
                "Automatic recovery is blocked."
            ),
        )
    )

    result = adapter.evaluate(
        payment=payment,
        orchestration=orchestration,
    )

    assert result.escalation is not None

    assert (
        result.escalation.decision.should_escalate
        is True
    )

    assert (
        result.escalation.escalation
        is not None
    )


def test_low_confidence_attempt_escalates():

    adapter = create_adapter()

    payment = create_payment()

    attempt = create_attempt(
        payment,
        probability=0.30,
    )

    orchestration = (
        RecoveryOrchestrationResult(
            attempt=attempt,
            policy_decision=None,
            executed=False,
            blocked=True,
            requires_approval=False,
            reason=(
                "Recovery execution blocked."
            ),
        )
    )

    result = adapter.evaluate(
        payment=payment,
        orchestration=orchestration,
    )

    assert result.escalation is not None

    assert (
        result.escalation.decision.should_escalate
        is True
    )

    assert (
        result.escalation.escalation
        is not None
    )


def test_missing_attempt_escalates():

    adapter = create_adapter()

    payment = create_payment()

    orchestration = (
        RecoveryOrchestrationResult(
            attempt=None,
            policy_decision=None,
            executed=False,
            blocked=True,
            requires_approval=False,
            reason=(
                "Payment is not eligible "
                "for recovery."
            ),
        )
    )

    result = adapter.evaluate(
        payment=payment,
        orchestration=orchestration,
    )

    assert result.escalation is not None

    assert (
        result.escalation.decision.should_escalate
        is True
    )

    assert (
        result.escalation.escalation
        is not None
    )