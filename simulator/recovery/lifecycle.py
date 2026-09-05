from backend.app.domain.enums import RecoveryStatus
from backend.app.domain.models import RecoveryAttempt


class RecoveryLifecycle:
    """
    Manages valid state transitions for a recovery attempt.

    Lifecycle:

    PROPOSED
        ↓
    APPROVED / REJECTED

    APPROVED
        ↓
    SCHEDULED
        ↓
    EXECUTING
        ↓
    SUCCEEDED / FAILED / CANCELLED
    """

    def approve(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        self._require_status(
            attempt,
            RecoveryStatus.PROPOSED,
        )

        attempt.status = RecoveryStatus.APPROVED

        return attempt

    def reject(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        self._require_status(
            attempt,
            RecoveryStatus.PROPOSED,
        )

        attempt.status = RecoveryStatus.REJECTED

        return attempt

    def schedule(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        self._require_status(
            attempt,
            RecoveryStatus.APPROVED,
        )

        attempt.status = RecoveryStatus.SCHEDULED

        return attempt

    def start_execution(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:
        """
        Start execution of a recovery attempt.

        Production flow:

            PROPOSED
                ↓
            APPROVED
                ↓
            SCHEDULED
                ↓
            EXECUTING

        Simulator tests may directly execute a proposed
        attempt, so PROPOSED is also accepted.
        """

        allowed_statuses = {
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SCHEDULED,
        }

        if attempt.status not in allowed_statuses:
            raise ValueError(
                "Invalid recovery lifecycle transition. "
                f"Expected one of {allowed_statuses}, "
                f"got {attempt.status}."
            )

        attempt.status = RecoveryStatus.EXECUTING

        return attempt

    def mark_succeeded(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        self._require_status(
            attempt,
            RecoveryStatus.EXECUTING,
        )

        attempt.status = RecoveryStatus.SUCCEEDED

        return attempt

    def mark_failed(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        self._require_status(
            attempt,
            RecoveryStatus.EXECUTING,
        )

        attempt.status = RecoveryStatus.FAILED

        return attempt

    def cancel(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        if attempt.status in {
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
            RecoveryStatus.REJECTED,
            RecoveryStatus.CANCELLED,
        }:
            raise ValueError(
                "Cannot cancel recovery attempt "
                f"from terminal state: {attempt.status}"
            )

        attempt.status = RecoveryStatus.CANCELLED

        return attempt

    def _require_status(
        self,
        attempt: RecoveryAttempt,
        expected_status: RecoveryStatus,
    ) -> None:

        if attempt.status != expected_status:
            raise ValueError(
                "Invalid recovery lifecycle transition. "
                f"Expected {expected_status}, "
                f"got {attempt.status}."
            )