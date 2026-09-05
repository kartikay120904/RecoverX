from uuid import uuid4

import pytest

from backend.app.domain.audit import AuditEventType
from simulator.audit.service import AuditService
from simulator.recovery.escalation import (
    EscalationService,
    EscalationStatus,
)


class FakePayment:
    def __init__(self) -> None:
        self.payment_id = uuid4()


class FakeRecoveryAttempt:
    def __init__(self) -> None:
        self.recovery_id = uuid4()


def test_escalation_is_created():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    payment = FakePayment()

    attempt = FakeRecoveryAttempt()

    escalation = escalation_service.escalate(
        payment=payment,
        attempt=attempt,
        reason="retry limit exceeded",
    )

    assert escalation.payment_id == (
        payment.payment_id
    )

    assert escalation.recovery_id == (
        attempt.recovery_id
    )

    assert escalation.reason == (
        "retry limit exceeded"
    )

    assert escalation.status == (
        EscalationStatus.OPEN
    )


def test_escalation_creates_audit_event():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    payment = FakePayment()

    escalation = escalation_service.escalate(
        payment=payment,
        reason="manual review required",
    )

    events = audit_service.events_for_payment(
        payment.payment_id
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == (
        AuditEventType.RECOVERY_ESCALATED
    )

    assert event.metadata["reason"] == (
        "manual review required"
    )

    assert event.metadata["escalation_id"] == (
        str(escalation.escalation_id)
    )


def test_escalation_can_be_resolved():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    payment = FakePayment()

    escalation = escalation_service.escalate(
        payment=payment,
        reason="high value payment",
    )

    resolved = escalation_service.resolve(
        escalation.escalation_id
    )

    assert resolved.status == (
        EscalationStatus.RESOLVED
    )


def test_escalation_can_be_rejected():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    payment = FakePayment()

    escalation = escalation_service.escalate(
        payment=payment,
        reason="recovery unsafe",
    )

    rejected = escalation_service.reject(
        escalation.escalation_id
    )

    assert rejected.status == (
        EscalationStatus.REJECTED
    )


def test_open_escalations_returns_only_open_items():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    payment_one = FakePayment()

    payment_two = FakePayment()

    escalation_one = (
        escalation_service.escalate(
            payment=payment_one,
            reason="retry limit exceeded",
        )
    )

    escalation_two = (
        escalation_service.escalate(
            payment=payment_two,
            reason="human approval required",
        )
    )

    escalation_service.resolve(
        escalation_one.escalation_id
    )

    open_escalations = (
        escalation_service.open_escalations()
    )

    assert len(open_escalations) == 1

    assert open_escalations[0].escalation_id == (
        escalation_two.escalation_id
    )


def test_unknown_escalation_cannot_be_resolved():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    with pytest.raises(ValueError):
        escalation_service.resolve(
            uuid4()
        )


def test_unknown_escalation_cannot_be_rejected():
    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service
    )

    with pytest.raises(ValueError):
        escalation_service.reject(
            uuid4()
        )