from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
    RecoveryEvent,
)


class RecoveryExecutionResult:
    """
    Result of executing a recovery attempt.

    Keeps execution output separate from the
    RecoveryAttempt model so the original
    decision record remains understandable.
    """

    def __init__(
        self,
        attempt: RecoveryAttempt,
        events: list[RecoveryEvent],
    ):
        self.attempt = attempt
        self.events = events


def can_transition(
    current_status: RecoveryStatus,
    next_status: RecoveryStatus,
) -> bool:
    """
    Validate recovery lifecycle transitions.
    """

    allowed_transitions = {
        RecoveryStatus.PROPOSED: {
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        },
        RecoveryStatus.SCHEDULED: {
            RecoveryStatus.EXECUTING,
            RecoveryStatus.CANCELLED,
        },
        RecoveryStatus.EXECUTING: {
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        },
        RecoveryStatus.SUCCEEDED: set(),
        RecoveryStatus.FAILED: set(),
        RecoveryStatus.CANCELLED: set(),
    }

    return next_status in allowed_transitions.get(
        current_status,
        set(),
    )


def create_recovery_event(
    payment_id,
    event_type: str,
    strategy: RecoveryStrategy | None = None,
    status: RecoveryStatus | None = None,
    details: str | None = None,
    metadata: dict | None = None,
) -> RecoveryEvent:
    """
    Create an immutable recovery lifecycle event.
    """

    return RecoveryEvent(
        payment_id=payment_id,
        event_type=event_type,
        strategy=strategy,
        status=status,
        details=details,
        metadata=metadata or {},
    )


def schedule_recovery(
    attempt: RecoveryAttempt,
) -> RecoveryEvent:
    """
    Schedule a proposed recovery attempt.
    """

    if not can_transition(
        attempt.status,
        RecoveryStatus.SCHEDULED,
    ):
        raise ValueError(
            f"Invalid transition from "
            f"{attempt.status} to "
            f"{RecoveryStatus.SCHEDULED}"
        )

    attempt.status = RecoveryStatus.SCHEDULED

    return create_recovery_event(
        payment_id=attempt.payment_id,
        event_type="recovery_scheduled",
        strategy=attempt.strategy,
        status=attempt.status,
        details="Recovery attempt scheduled.",
    )


def start_recovery(
    attempt: RecoveryAttempt,
) -> RecoveryEvent:
    """
    Mark a scheduled recovery as executing.
    """

    if not can_transition(
        attempt.status,
        RecoveryStatus.EXECUTING,
    ):
        raise ValueError(
            f"Invalid transition from "
            f"{attempt.status} to "
            f"{RecoveryStatus.EXECUTING}"
        )

    attempt.status = RecoveryStatus.EXECUTING

    return create_recovery_event(
        payment_id=attempt.payment_id,
        event_type="recovery_execution_started",
        strategy=attempt.strategy,
        status=attempt.status,
        details="Recovery execution started.",
    )


def should_recovery_succeed(
    attempt: RecoveryAttempt,
) -> bool:
    """
    Deterministic recovery outcome.

    This intentionally avoids randomness so
    simulations and tests remain reproducible.

    A recovery succeeds when the predicted
    probability is at least 0.50.
    """

    return (
        attempt.predicted_probability
        >= 0.50
    )


def complete_recovery(
    payment: Payment,
    attempt: RecoveryAttempt,
) -> RecoveryEvent:
    """
    Complete an executing recovery attempt.
    """

    if attempt.status != RecoveryStatus.EXECUTING:
        raise ValueError(
            "Recovery attempt must be executing "
            "before completion."
        )

    succeeded = should_recovery_succeed(
        attempt,
    )

    if succeeded:

        attempt.status = (
            RecoveryStatus.SUCCEEDED
        )

        attempt.actual_revenue = (
            payment.amount
        )

        return create_recovery_event(
            payment_id=payment.payment_id,
            event_type="recovery_succeeded",
            strategy=attempt.strategy,
            status=attempt.status,
            details=(
                "Payment recovery succeeded."
            ),
            metadata={
                "actual_revenue": float(
                    attempt.actual_revenue
                ),
            },
        )

    attempt.status = RecoveryStatus.FAILED

    attempt.actual_revenue = Decimal("0")

    return create_recovery_event(
        payment_id=payment.payment_id,
        event_type="recovery_failed",
        strategy=attempt.strategy,
        status=attempt.status,
        details="Payment recovery failed.",
        metadata={
            "actual_revenue": 0,
        },
    )


def cancel_recovery(
    attempt: RecoveryAttempt,
) -> RecoveryEvent:
    """
    Cancel a proposed or scheduled recovery.
    """

    if not can_transition(
        attempt.status,
        RecoveryStatus.CANCELLED,
    ):
        raise ValueError(
            f"Invalid transition from "
            f"{attempt.status} to "
            f"{RecoveryStatus.CANCELLED}"
        )

    attempt.status = RecoveryStatus.CANCELLED

    return create_recovery_event(
        payment_id=attempt.payment_id,
        event_type="recovery_cancelled",
        strategy=attempt.strategy,
        status=attempt.status,
        details="Recovery attempt cancelled.",
    )


def execute_recovery(
    payment: Payment,
    attempt: RecoveryAttempt,
) -> RecoveryExecutionResult:
    """
    Execute the complete recovery lifecycle.

    PROPOSED
        ->
    SCHEDULED
        ->
    EXECUTING
        ->
    SUCCEEDED / FAILED
    """

    events: list[RecoveryEvent] = []

    if attempt.status == RecoveryStatus.PROPOSED:

        events.append(
            schedule_recovery(
                attempt,
            )
        )

    if attempt.status == RecoveryStatus.SCHEDULED:

        events.append(
            start_recovery(
                attempt,
            )
        )

    if attempt.status == RecoveryStatus.EXECUTING:

        events.append(
            complete_recovery(
                payment,
                attempt,
            )
        )

    return RecoveryExecutionResult(
        attempt=attempt,
        events=events,
    )