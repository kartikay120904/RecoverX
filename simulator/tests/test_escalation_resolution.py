from decimal import Decimal
from uuid import uuid4

import pytest

from backend.app.domain.audit import (
    AuditEventType,
)

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
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

from simulator.recovery.escalation_resolution import (
    EscalationResolutionWorkflow,
)


def create_payment() -> Payment:

    return Payment(
        amount=Decimal("1000.00"),
        method=PaymentMethod.CARD,
        status=PaymentStatus.FAILED,
        failure_code="payment_declined",
    )


def create_workflow():

    audit_service = AuditService()

    escalation_service = EscalationService(
        audit_service=audit_service
    )

    workflow = EscalationResolutionWorkflow(
        escalation_service=escalation_service,
        audit_service=audit_service,
    )

    return (
        workflow,
        escalation_service,
        audit_service,
    )


def test_approve_open_escalation():

    (
        workflow,
        escalation_service,
        audit_service,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    result = workflow.approve(
        escalation.escalation_id
    )

    assert result.approved is True

    assert (
        result.escalation.status
        == EscalationStatus.RESOLVED
    )


def test_approve_records_audit_event():

    (
        workflow,
        escalation_service,
        audit_service,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    workflow.approve(
        escalation.escalation_id,
        reason="Human approved recovery.",
    )

    events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    approval_events = [
        event
        for event in events
        if event.event_type
        == AuditEventType.RECOVERY_APPROVED
    ]

    assert len(approval_events) == 1

    assert (
        approval_events[0]
        .metadata["reason"]
        == "Human approved recovery."
    )


def test_reject_open_escalation():

    (
        workflow,
        escalation_service,
        audit_service,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    result = workflow.reject(
        escalation.escalation_id
    )

    assert result.approved is False

    assert (
        result.escalation.status
        == EscalationStatus.REJECTED
    )


def test_reject_records_audit_event():

    (
        workflow,
        escalation_service,
        audit_service,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Manual review required.",
        )
    )

    workflow.reject(
        escalation.escalation_id,
        reason="Human rejected recovery.",
    )

    events = (
        audit_service.events_for_payment(
            payment.payment_id
        )
    )

    rejection_events = [
        event
        for event in events
        if event.event_type
        == AuditEventType.RECOVERY_FAILED
    ]

    assert len(rejection_events) == 1

    assert (
        rejection_events[0]
        .metadata["reason"]
        == "Human rejected recovery."
    )


def test_cannot_approve_unknown_escalation():

    (
        workflow,
        _,
        _,
    ) = create_workflow()

    with pytest.raises(
        ValueError,
        match="Escalation not found",
    ):

        workflow.approve(
            uuid4()
        )


def test_cannot_reject_unknown_escalation():

    (
        workflow,
        _,
        _,
    ) = create_workflow()

    with pytest.raises(
        ValueError,
        match="Escalation not found",
    ):

        workflow.reject(
            uuid4()
        )


def test_cannot_approve_resolved_escalation():

    (
        workflow,
        escalation_service,
        _,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Review.",
        )
    )

    workflow.approve(
        escalation.escalation_id
    )

    with pytest.raises(
        ValueError,
        match="Only open escalations",
    ):

        workflow.approve(
            escalation.escalation_id
        )


def test_cannot_reject_rejected_escalation():

    (
        workflow,
        escalation_service,
        _,
    ) = create_workflow()

    payment = create_payment()

    escalation = (
        escalation_service.escalate(
            payment=payment,
            reason="Review.",
        )
    )

    workflow.reject(
        escalation.escalation_id
    )

    with pytest.raises(
        ValueError,
        match="Only open escalations",
    ):

        workflow.reject(
            escalation.escalation_id
        )