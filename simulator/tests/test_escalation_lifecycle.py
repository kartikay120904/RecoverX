from decimal import Decimal

import pytest

from backend.app.domain.audit import (
    AuditEventType,
)
from backend.app.domain.enums import (
    PaymentMethod,
)
from backend.app.domain.models import (
    Payment,
)
from simulator.audit.service import (
    AuditService,
)
from simulator.recovery.escalation import (
    EscalationService,
    EscalationStatus,
)


def create_payment() -> Payment:
    return Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
    )


def test_resolve_escalation_updates_status():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    resolved = (
        escalation_service.resolve(
            escalation.escalation_id
        )
    )

    assert (
        resolved.status
        == EscalationStatus.RESOLVED
    )


def test_resolving_escalation_creates_audit_event():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    escalation_service.resolve(
        escalation.escalation_id
    )

    events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        AuditEventType.RECOVERY_ESCALATED
        in event_types
    )

    assert (
        AuditEventType.ESCALATION_RESOLVED
        in event_types
    )


def test_reject_escalation_updates_status():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    rejected = (
        escalation_service.reject(
            escalation.escalation_id
        )
    )

    assert (
        rejected.status
        == EscalationStatus.REJECTED
    )


def test_rejecting_escalation_creates_audit_event():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    escalation_service.reject(
        escalation.escalation_id
    )

    events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    event_types = [
        event.event_type
        for event in events
    ]

    assert (
        AuditEventType.RECOVERY_ESCALATED
        in event_types
    )

    assert (
        AuditEventType.ESCALATION_REJECTED
        in event_types
    )


def test_resolved_escalation_cannot_be_rejected():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
        )
    )

    escalation_service.resolve(
        escalation.escalation_id
    )

    with pytest.raises(
        ValueError
    ):
        escalation_service.reject(
            escalation.escalation_id
        )


def test_rejected_escalation_cannot_be_resolved():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
        )
    )

    escalation_service.reject(
        escalation.escalation_id
    )

    with pytest.raises(
        ValueError
    ):
        escalation_service.resolve(
            escalation.escalation_id
        )


def test_closed_escalation_is_not_open():
    audit_service = AuditService()

    escalation_service = (
        EscalationService(
            audit_service
        )
    )

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
        )
    )

    escalation_service.resolve(
        escalation.escalation_id
    )

    open_escalations = (
        escalation_service.open_escalations()
    )

    assert escalation not in open_escalations