from uuid import uuid4

from backend.app.domain.audit import AuditEventType
from simulator.audit.presentation import AuditPresenter
from simulator.audit.service import AuditService


def test_payment_timeline_returns_events():
    audit_service = AuditService()

    payment_id = uuid4()

    audit_service.record(
        event_type=AuditEventType.PAYMENT_DETECTED,
        payment_id=payment_id,
    )

    presenter = AuditPresenter(
        audit_service
    )

    result = presenter.build_payment_timeline(
        payment_id
    )

    assert result["payment_id"] == str(payment_id)
    assert result["event_count"] == 1
    assert len(result["timeline"]) == 1


def test_recovery_timeline_returns_events():
    audit_service = AuditService()

    payment_id = uuid4()
    recovery_id = uuid4()

    audit_service.record(
        event_type=AuditEventType.RECOVERY_PROPOSED,
        payment_id=payment_id,
        recovery_id=recovery_id,
    )

    presenter = AuditPresenter(
        audit_service
    )

    result = presenter.build_recovery_timeline(
        recovery_id
    )

    assert result["recovery_id"] == str(recovery_id)
    assert result["event_count"] == 1
    assert len(result["timeline"]) == 1


def test_unified_timeline_combines_payment_and_recovery_events():
    audit_service = AuditService()

    payment_id = uuid4()
    recovery_id = uuid4()

    audit_service.record(
        event_type=AuditEventType.PAYMENT_DETECTED,
        payment_id=payment_id,
    )

    audit_service.record(
        event_type=AuditEventType.RECOVERY_PROPOSED,
        payment_id=payment_id,
        recovery_id=recovery_id,
    )

    presenter = AuditPresenter(
        audit_service
    )

    result = presenter.build_unified_timeline(
        payment_id=payment_id,
        recovery_id=recovery_id,
    )

    assert result["event_count"] == 2
    assert len(result["timeline"]) == 2


def test_timeline_is_chronological():
    audit_service = AuditService()

    payment_id = uuid4()

    audit_service.record(
        event_type=AuditEventType.PAYMENT_DETECTED,
        payment_id=payment_id,
    )

    audit_service.record(
        event_type=AuditEventType.RECOVERY_PROPOSED,
        payment_id=payment_id,
    )

    presenter = AuditPresenter(
        audit_service
    )

    result = presenter.build_payment_timeline(
        payment_id
    )

    timestamps = [
        event["timestamp"]
        for event in result["timeline"]
    ]

    assert timestamps == sorted(timestamps)