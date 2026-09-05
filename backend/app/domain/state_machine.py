from uuid import UUID, uuid4

from .enums import PaymentStatus, RecoveryStatus
from .events import DomainEvent
from .models import Payment


# =========================================================
# Exceptions
# =========================================================

class InvalidPaymentTransition(Exception):
    """Raised when a payment attempts an invalid state transition."""


class InvalidRecoveryTransition(Exception):
    """Raised when a recovery attempts an invalid state transition."""


# =========================================================
# Payment State Machine
# =========================================================

ALLOWED_PAYMENT_TRANSITIONS: dict[
    PaymentStatus,
    set[PaymentStatus],
] = {
    PaymentStatus.CREATED: {
        PaymentStatus.AUTHORIZED,
        PaymentStatus.FAILED,
    },

    PaymentStatus.AUTHORIZED: {
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED,
    },

    PaymentStatus.CAPTURED: {
        PaymentStatus.REFUNDED,
    },

    PaymentStatus.FAILED: {
        PaymentStatus.RETRY_ELIGIBLE,
    },

    PaymentStatus.RETRY_ELIGIBLE: {
        PaymentStatus.RETRYING,
    },

    PaymentStatus.RETRYING: {
        PaymentStatus.CAPTURED,
        PaymentStatus.FAILED,
    },

    PaymentStatus.REFUNDED: set(),
}


# =========================================================
# Recovery State Machine
# =========================================================

ALLOWED_RECOVERY_TRANSITIONS: dict[
    RecoveryStatus,
    set[RecoveryStatus],
] = {
    # A recovery decision has been created.
    RecoveryStatus.PROPOSED: {
        RecoveryStatus.APPROVED,
        RecoveryStatus.SCHEDULED,
        RecoveryStatus.EXECUTING,
        RecoveryStatus.REJECTED,
        RecoveryStatus.CANCELLED,
    },

    # Approved recoveries can be scheduled or executed.
    RecoveryStatus.APPROVED: {
        RecoveryStatus.SCHEDULED,
        RecoveryStatus.EXECUTING,
        RecoveryStatus.REJECTED,
        RecoveryStatus.CANCELLED,
    },

    # Scheduled recoveries wait for execution.
    RecoveryStatus.SCHEDULED: {
        RecoveryStatus.EXECUTING,
        RecoveryStatus.CANCELLED,
        RecoveryStatus.REJECTED,
    },

    # Recovery is actively being attempted.
    RecoveryStatus.EXECUTING: {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
        RecoveryStatus.CANCELLED,
    },

    # Terminal states.
    RecoveryStatus.SUCCEEDED: set(),
    RecoveryStatus.FAILED: set(),
    RecoveryStatus.REJECTED: set(),
    RecoveryStatus.CANCELLED: set(),
}


# =========================================================
# Normalization Helpers
# =========================================================

def _normalize_payment_status(
    status: PaymentStatus | str,
) -> PaymentStatus:
    """
    Normalize a PaymentStatus enum or string into PaymentStatus.
    """

    if isinstance(status, PaymentStatus):
        return status

    try:
        return PaymentStatus(status)
    except (ValueError, TypeError) as exc:
        raise InvalidPaymentTransition(
            f"Unknown payment status: {status}"
        ) from exc


def _normalize_recovery_status(
    status: RecoveryStatus | str,
) -> RecoveryStatus:
    """
    Normalize a RecoveryStatus enum or string into RecoveryStatus.
    """

    if isinstance(status, RecoveryStatus):
        return status

    try:
        return RecoveryStatus(status)
    except (ValueError, TypeError) as exc:
        raise InvalidRecoveryTransition(
            f"Unknown recovery status: {status}"
        ) from exc


# =========================================================
# Payment Transition
# =========================================================

def transition_payment(
    payment: Payment,
    new_status: PaymentStatus | str,
    *,
    actor: str,
    correlation_id: UUID | None = None,
) -> DomainEvent:
    """
    Transition a payment to a new valid status.

    Raises:
        InvalidPaymentTransition:
            If the requested transition is not allowed.
    """

    current_status = _normalize_payment_status(
        payment.status
    )

    target_status = _normalize_payment_status(
        new_status
    )

    allowed = ALLOWED_PAYMENT_TRANSITIONS.get(
        current_status,
        set(),
    )

    if target_status not in allowed:
        raise InvalidPaymentTransition(
            "Invalid payment transition: "
            f"{current_status.value} -> "
            f"{target_status.value}"
        )

    previous_status = current_status

    payment.status = target_status

    if correlation_id is None:
        correlation_id = uuid4()

    return DomainEvent(
        event_type="payment.status_changed",
        entity_id=payment.payment_id,
        correlation_id=correlation_id,
        actor=actor,
        payload={
            "previous_status": previous_status.value,
            "new_status": target_status.value,
            "attempt_number": getattr(
                payment,
                "attempt_number",
                None,
            ),
        },
    )


# =========================================================
# Recovery Transition
# =========================================================

def transition_recovery(
    recovery,
    new_status: RecoveryStatus | str,
    *,
    actor: str = "system",
    correlation_id: UUID | None = None,
) -> DomainEvent:
    """
    Transition a recovery attempt to a new valid status.

    Supports decision, approval, scheduling and execution
    stages of the recovery lifecycle.

    Raises:
        InvalidRecoveryTransition:
            If the requested transition is not allowed.
    """

    current_status = _normalize_recovery_status(
        recovery.status
    )

    target_status = _normalize_recovery_status(
        new_status
    )

    allowed = ALLOWED_RECOVERY_TRANSITIONS.get(
        current_status,
        set(),
    )

    if target_status not in allowed:
        raise InvalidRecoveryTransition(
            "Invalid recovery transition: "
            f"{current_status.value} -> "
            f"{target_status.value}"
        )

    previous_status = current_status

    recovery.status = target_status

    if correlation_id is None:
        correlation_id = uuid4()

    entity_id = getattr(
        recovery,
        "payment_id",
        None,
    )

    return DomainEvent(
        event_type="recovery.status_changed",
        entity_id=entity_id,
        correlation_id=correlation_id,
        actor=actor,
        payload={
            "previous_status": previous_status.value,
            "new_status": target_status.value,
        },
    )


# =========================================================
# Validation Helpers
# =========================================================

def can_transition_payment(
    current_status: PaymentStatus | str,
    new_status: PaymentStatus | str,
) -> bool:
    """
    Return True if a payment transition is allowed.
    """

    try:
        current = _normalize_payment_status(
            current_status
        )

        target = _normalize_payment_status(
            new_status
        )

        return target in ALLOWED_PAYMENT_TRANSITIONS.get(
            current,
            set(),
        )

    except InvalidPaymentTransition:
        return False


def can_transition_recovery(
    current_status: RecoveryStatus | str,
    new_status: RecoveryStatus | str,
) -> bool:
    """
    Return True if a recovery transition is allowed.
    """

    try:
        current = _normalize_recovery_status(
            current_status
        )

        target = _normalize_recovery_status(
            new_status
        )

        return target in ALLOWED_RECOVERY_TRANSITIONS.get(
            current,
            set(),
        )

    except InvalidRecoveryTransition:
        return False


# =========================================================
# Terminal State Helpers
# =========================================================

def is_terminal_payment_status(
    status: PaymentStatus | str,
) -> bool:
    """
    Return True if the payment status cannot transition further.
    """

    normalized_status = _normalize_payment_status(
        status
    )

    return len(
        ALLOWED_PAYMENT_TRANSITIONS.get(
            normalized_status,
            set(),
        )
    ) == 0


def is_terminal_recovery_status(
    status: RecoveryStatus | str,
) -> bool:
    """
    Return True if the recovery status cannot transition further.
    """

    normalized_status = _normalize_recovery_status(
        status
    )

    return len(
        ALLOWED_RECOVERY_TRANSITIONS.get(
            normalized_status,
            set(),
        )
    ) == 0