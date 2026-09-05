from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from integrations.recovery.recovery_store import (
    RecoveryStore,
)


def create_recovery_attempt(
    payment_id,
) -> RecoveryAttempt:
    """
    Create a lightweight recovery attempt
    for testing.
    """

    return RecoveryAttempt(
        payment_id=payment_id,
        strategy=RecoveryStrategy.RECOVERY_LINK,
        predicted_probability=0.75,
        predicted_revenue=Decimal("500.00"),
    )


def test_register_attempt():
    """
    A recovery attempt should be stored and
    retrievable by payment ID.
    """

    store = RecoveryStore()

    payment_id = uuid4()

    attempt = create_recovery_attempt(
        payment_id
    )

    store.register_attempt(
        attempt
    )

    stored_attempt = store.get_attempt(
        payment_id
    )

    assert stored_attempt is attempt


def test_complete_recovery_updates_attempt():
    """
    Completing a recovery should update the
    attempt with actual recovered revenue and
    a successful status.
    """

    store = RecoveryStore()

    payment_id = uuid4()

    attempt = create_recovery_attempt(
        payment_id
    )

    store.register_attempt(
        attempt
    )

    result = store.complete_recovery(
        payment_id=payment_id,
        actual_revenue=Decimal("500.00"),
        payment_link_id="plink_test_123",
    )

    assert result is attempt

    assert result.actual_revenue == Decimal(
        "500.00"
    )

    assert result.status == (
        RecoveryStatus.SUCCEEDED
    )


def test_complete_recovery_creates_audit_event():
    """
    A completed recovery should create an
    immutable lifecycle audit event.
    """

    store = RecoveryStore()

    payment_id = uuid4()

    attempt = create_recovery_attempt(
        payment_id
    )

    store.register_attempt(
        attempt
    )

    store.complete_recovery(
        payment_id=payment_id,
        actual_revenue=Decimal("250.00"),
        payment_link_id="plink_test_audit",
    )

    events = store.get_events(
        payment_id
    )

    assert len(events) == 1

    event = events[0]

    assert (
        event.event_type
        == "recovery.completed"
    )

    assert event.status == (
        RecoveryStatus.SUCCEEDED
    )

    assert (
        event.metadata[
            "payment_link_id"
        ]
        == "plink_test_audit"
    )

    assert (
        event.metadata[
            "actual_revenue"
        ]
        == "250.00"
    )


def test_unknown_payment_does_not_create_completion():
    """
    Completing an unknown payment should not
    crash or create a recovery event.
    """

    store = RecoveryStore()

    unknown_payment_id = uuid4()

    result = store.complete_recovery(
        payment_id=unknown_payment_id,
        actual_revenue=Decimal("100.00"),
        payment_link_id="plink_unknown",
    )

    assert result is None

    events = store.get_events(
        unknown_payment_id
    )

    assert events == []