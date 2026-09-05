from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from backend.app.domain.audit import (
    AuditEventType,
)

from simulator.audit.service import AuditService
from simulator.recovery.escalation_policy import (
    EscalationPolicy,
)
from simulator.recovery.orchestrator import (
    RecoveryOrchestrator,
)


def make_payment(
    amount: float = 1000.0,
) -> Payment:
    return Payment(
        payment_id=uuid4(),
        amount=amount,
        method="upi",
    )


def make_attempt(
    payment_id,
) -> RecoveryAttempt:
    return RecoveryAttempt(
        payment_id=payment_id,
        strategy="retry",
        status=RecoveryStatus.PROPOSED,
        reason="Test recovery attempt.",
        predicted_revenue=100.0,
    )


def make_orchestrator() -> tuple[
    RecoveryOrchestrator,
    AuditService,
]:
    audit_service = AuditService()

    orchestrator = RecoveryOrchestrator(
        audit_service=audit_service,
        escalation_policy=EscalationPolicy(),
    )

    return orchestrator, audit_service


def test_no_recovery_action_automatically_escalates():

    orchestrator, audit_service = (
        make_orchestrator()
    )

    payment = make_payment()

    escalation = (
        orchestrator.evaluate_escalation(
            payment=payment,
            has_recovery_action=False,
        )
    )

    assert escalation is not None
    assert escalation.payment_id == (
        payment.payment_id
    )
    assert escalation.reason == (
        "no recovery action available"
    )

    events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    assert len(events) == 1
    assert events[0].event_type == (
        AuditEventType.RECOVERY_ESCALATED
    )


def test_low_confidence_automatically_escalates():

    orchestrator, _ = make_orchestrator()

    payment = make_payment()

    escalation = (
        orchestrator.evaluate_escalation(
            payment=payment,
            confidence=0.2,
            minimum_confidence=0.5,
        )
    )

    assert escalation is not None
    assert escalation.reason == (
        "recovery confidence too low"
    )


def test_human_approval_automatically_escalates():

    orchestrator, _ = make_orchestrator()

    payment = make_payment()

    escalation = (
        orchestrator.evaluate_escalation(
            payment=payment,
            requires_human_approval=True,
        )
    )

    assert escalation is not None
    assert escalation.reason == (
        "recovery requires human approval"
    )


def test_high_value_payment_automatically_escalates():

    orchestrator, _ = make_orchestrator()

    payment = make_payment(
        amount=100000.0,
    )

    escalation = (
        orchestrator.evaluate_escalation(
            payment=payment,
            high_value_threshold=50000.0,
        )
    )

    assert escalation is not None
    assert escalation.reason == (
        "high-value payment requires review"
    )


def test_retry_limit_automatically_escalates():

    orchestrator, _ = make_orchestrator()

    payment = make_payment()

    escalation = (
        orchestrator.evaluate_escalation(
            payment=payment,
            retry_limit_reached=True,
        )
    )

    assert escalation is not None
    assert escalation.reason == (
        "retry limit exceeded"
    )


def test_first_execution_failure_does_not_escalate():

    orchestrator, _ = make_orchestrator()

    payment = make_payment()

    attempt = make_attempt(
        payment.payment_id
    )

    attempt = orchestrator.start_execution(
        attempt
    )

    result = orchestrator.mark_failed(
        attempt=attempt,
        payment=payment,
    )

    assert result.status == (
        RecoveryStatus.FAILED
    )

    escalations = (
        orchestrator.escalation_service
        .all_escalations()
    )

    assert len(escalations) == 0


def test_repeated_execution_failures_automatically_escalate():

    orchestrator, audit_service = (
        make_orchestrator()
    )

    payment = make_payment()

    first_attempt = make_attempt(
        payment.payment_id
    )

    first_attempt = (
        orchestrator.start_execution(
            first_attempt
        )
    )

    orchestrator.mark_failed(
        attempt=first_attempt,
        payment=payment,
    )

    second_attempt = make_attempt(
        payment.payment_id
    )

    second_attempt = (
        orchestrator.start_execution(
            second_attempt
        )
    )

    orchestrator.mark_failed(
        attempt=second_attempt,
        payment=payment,
    )

    escalations = (
        orchestrator.escalation_service
        .all_escalations()
    )

    assert len(escalations) == 1

    escalation = escalations[0]

    assert escalation.payment_id == (
        payment.payment_id
    )

    assert escalation.reason == (
        "recovery execution repeatedly failed"
    )

    audit_events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    escalation_events = [
        event
        for event in audit_events
        if event.event_type
        == AuditEventType.RECOVERY_ESCALATED
    ]

    assert len(escalation_events) == 1


def test_successful_recovery_does_not_escalate():

    orchestrator, _ = make_orchestrator()

    payment = make_payment()

    attempt = make_attempt(
        payment.payment_id
    )

    attempt = (
        orchestrator.start_execution(
            attempt
        )
    )

    result = orchestrator.mark_succeeded(
        attempt
    )

    assert result.status == (
        RecoveryStatus.SUCCEEDED
    )

    escalations = (
        orchestrator.escalation_service
        .all_escalations()
    )

    assert len(escalations) == 0