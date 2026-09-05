from backend.app.domain.enums import (
    RecoveryStatus,
)

from backend.app.domain.models import (
    RecoveryAttempt,
)

from backend.app.services.recovery_event_service import (
    RecoveryEventService,
    recovery_event_service,
)


class RecoveryApprovalService:
    """
    Handles explicit approval or rejection of
    proposed recovery attempts.

    This service is intentionally isolated and does
    not modify the existing recovery execution flow.
    """

    def __init__(
        self,
        event_service: RecoveryEventService | None = None,
    ) -> None:

        self.event_service = (
            event_service
            or recovery_event_service
        )

    def approve(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:
        """
        Approve a proposed recovery attempt.
        """

        if (
            attempt.status
            != RecoveryStatus.PROPOSED
        ):
            raise ValueError(
                "Only proposed recovery attempts "
                "can be approved."
            )

        attempt.status = (
            RecoveryStatus.APPROVED
        )

        self.event_service.record_event(
            payment_id=attempt.payment_id,
            event_type="recovery_approved",
            strategy=attempt.strategy,
            status=attempt.status,
            details=(
                "Recovery attempt approved "
                "for execution."
            ),
            metadata={
                "recovery_id": str(
                    attempt.recovery_id
                ),
            },
        )

        return attempt

    def reject(
        self,
        attempt: RecoveryAttempt,
        reason: str = "Recovery attempt rejected.",
    ) -> RecoveryAttempt:
        """
        Reject a proposed recovery attempt.
        """

        if (
            attempt.status
            != RecoveryStatus.PROPOSED
        ):
            raise ValueError(
                "Only proposed recovery attempts "
                "can be rejected."
            )

        attempt.status = (
            RecoveryStatus.REJECTED
        )

        self.event_service.record_event(
            payment_id=attempt.payment_id,
            event_type="recovery_rejected",
            strategy=attempt.strategy,
            status=attempt.status,
            details=reason,
            metadata={
                "recovery_id": str(
                    attempt.recovery_id
                ),
            },
        )

        return attempt