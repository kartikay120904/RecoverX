from decimal import Decimal

import pytest

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
)

from backend.app.domain.models import (
    Payment,
)

from backend.app.services.recovery_approval import (
    RecoveryApprovalService,
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


def test_approve_proposed_recovery():

    payment = create_payment()

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    approval_service = (
        RecoveryApprovalService()
    )

    attempt = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    approved_attempt = (
        approval_service.approve(
            attempt
        )
    )

    assert (
        approved_attempt.status
        == RecoveryStatus.APPROVED
    )


def test_reject_proposed_recovery():

    payment = create_payment()

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    approval_service = (
        RecoveryApprovalService()
    )

    attempt = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    rejected_attempt = (
        approval_service.reject(
            attempt,
            reason="Manual review rejected.",
        )
    )

    assert (
        rejected_attempt.status
        == RecoveryStatus.REJECTED
    )


def test_cannot_approve_non_proposed_recovery():

    payment = create_payment()

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    approval_service = (
        RecoveryApprovalService()
    )

    attempt = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    approval_service.approve(
        attempt
    )

    with pytest.raises(
        ValueError
    ):

        approval_service.approve(
            attempt
        )


def test_cannot_reject_approved_recovery():

    payment = create_payment()

    lifecycle_service = (
        RecoveryLifecycleService()
    )

    approval_service = (
        RecoveryApprovalService()
    )

    attempt = (
        lifecycle_service.propose_recovery(
            payment
        )
    )

    approval_service.approve(
        attempt
    )

    with pytest.raises(
        ValueError
    ):

        approval_service.reject(
            attempt
        )