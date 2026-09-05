from backend.app.domain.audit import (
    AuditEventType,
)

from simulator.recovery.runner import (
    RecoverySimulationRunner,
)


def test_runner_records_audit_events():

    runner = RecoverySimulationRunner(
        seed=42
    )

    attempts = runner.run(5)

    events = runner.audit_service.all_events()

    assert len(events) > 0

    event_types = {
        event.event_type
        for event in events
    }

    assert (
        AuditEventType.PAYMENT_DETECTED
        in event_types
    )

    if attempts:

        assert (
            AuditEventType.RECOVERY_PROPOSED
            in event_types
        )

        assert (
            AuditEventType.RECOVERY_APPROVED
            in event_types
        )

        assert (
            AuditEventType.RECOVERY_SCHEDULED
            in event_types
        )

        assert (
            AuditEventType.RECOVERY_EXECUTION_STARTED
            in event_types
        )


def test_completed_recoveries_have_terminal_audit_event():

    runner = RecoverySimulationRunner(
        seed=42
    )

    attempts = runner.run(10)

    events = runner.audit_service.all_events()

    terminal_events = [
        event
        for event in events
        if event.event_type in {
            AuditEventType.RECOVERY_SUCCEEDED,
            AuditEventType.RECOVERY_FAILED,
        }
    ]

    assert len(terminal_events) == len(
        attempts
    )


def test_audit_events_can_be_queried_by_payment():

    runner = RecoverySimulationRunner(
        seed=42
    )

    runner.run(5)

    events = runner.audit_service.all_events()

    assert len(events) > 0

    payment_id = events[0].payment_id

    payment_events = (
        runner.audit_service.events_for_payment(
            payment_id
        )
    )

    assert len(payment_events) > 0

    assert all(
        event.payment_id == payment_id
        for event in payment_events
    )


def test_audit_events_can_be_queried_by_recovery():

    runner = RecoverySimulationRunner(
        seed=42
    )

    runner.run(10)

    events = runner.audit_service.all_events()

    recovery_events = [
        event
        for event in events
        if event.recovery_id is not None
    ]

    if recovery_events:

        recovery_id = (
            recovery_events[0].recovery_id
        )

        matched_events = (
            runner.audit_service.events_for_recovery(
                recovery_id
            )
        )

        assert len(matched_events) > 0

        assert all(
            event.recovery_id == recovery_id
            for event in matched_events
        )