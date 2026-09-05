from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
)

from backend.app.domain.models import (
    Payment,
)

from backend.app.services.recovery_attempt_store import (
    RecoveryAttemptStore,
)

from backend.app.services.recovery_lifecycle import (
    RecoveryLifecycleService,
)


def create_payment() -> Payment:

    return Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.CARD,
        status=PaymentStatus.FAILED,
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT
        ),
        attempt_number=1,
    )


def create_attempt():

    payment = create_payment()

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    attempt = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    return payment, attempt


def test_save_and_get_recovery_attempt():

    store = RecoveryAttemptStore()

    _, attempt = create_attempt()

    store.save(
        attempt
    )

    stored_attempt = (
        store.get(
            attempt.recovery_id
        )
    )

    assert stored_attempt is attempt


def test_get_recovery_attempts_for_payment():

    store = RecoveryAttemptStore()

    payment, attempt_one = (
        create_attempt()
    )

    store.save(
        attempt_one
    )

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    attempt_two = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    store.save(
        attempt_two
    )

    attempts = (
        store.get_for_payment(
            payment.payment_id
        )
    )

    assert len(attempts) == 2


def test_get_latest_recovery_attempt():

    store = RecoveryAttemptStore()

    payment, attempt_one = (
        create_attempt()
    )

    store.save(
        attempt_one
    )

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    attempt_two = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    store.save(
        attempt_two
    )

    latest = (
        store.get_latest_for_payment(
            payment.payment_id
        )
    )

    assert latest is attempt_two


def test_get_recovery_attempts_by_status():

    store = RecoveryAttemptStore()

    _, attempt = create_attempt()

    store.save(
        attempt
    )

    attempts = (
        store.get_by_status(
            RecoveryStatus.PROPOSED
        )
    )

    assert len(attempts) == 1

    assert attempts[0] is attempt


def test_update_existing_recovery_attempt():

    store = RecoveryAttemptStore()

    _, attempt = create_attempt()

    store.save(
        attempt
    )

    attempt.status = (
        RecoveryStatus.APPROVED
    )

    store.save(
        attempt
    )

    assert store.count() == 1

    stored_attempt = (
        store.get(
            attempt.recovery_id
        )
    )

    assert (
        stored_attempt.status
        == RecoveryStatus.APPROVED
    )


def test_delete_recovery_attempt():

    store = RecoveryAttemptStore()

    _, attempt = create_attempt()

    store.save(
        attempt
    )

    deleted = (
        store.delete(
            attempt.recovery_id
        )
    )

    assert deleted is True

    assert (
        store.get(
            attempt.recovery_id
        )
        is None
    )

    assert store.count() == 0