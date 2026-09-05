from uuid import UUID

from backend.app.domain.enums import (
    RecoveryStatus,
)

from backend.app.domain.models import (
    RecoveryAttempt,
)


class RecoveryAttemptStore:
    """
    In-memory store for recovery attempts.

    This service is intentionally isolated so existing
    recovery, approval, execution, and API behavior is
    not affected.

    The store can later be replaced by PostgreSQL,
    Redis, or another persistence layer without changing
    callers that use this interface.
    """

    def __init__(self) -> None:
        self._attempts_by_recovery_id: dict[
            UUID,
            RecoveryAttempt,
        ] = {}

        self._recovery_ids_by_payment_id: dict[
            UUID,
            list[UUID],
        ] = {}

    def save(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:
        """
        Save or update a recovery attempt.

        Saving the same recovery_id again updates the
        stored attempt without duplicating its payment
        index entry.
        """

        existing = (
            attempt.recovery_id
            in self._attempts_by_recovery_id
        )

        self._attempts_by_recovery_id[
            attempt.recovery_id
        ] = attempt

        if not existing:

            self._recovery_ids_by_payment_id.setdefault(
                attempt.payment_id,
                [],
            ).append(
                attempt.recovery_id
            )

        return attempt

    def get(
        self,
        recovery_id: UUID,
    ) -> RecoveryAttempt | None:
        """
        Return a recovery attempt by recovery ID.
        """

        return (
            self._attempts_by_recovery_id.get(
                recovery_id
            )
        )

    def get_for_payment(
        self,
        payment_id: UUID,
    ) -> list[RecoveryAttempt]:
        """
        Return all recovery attempts for a payment.
        """

        recovery_ids = (
            self._recovery_ids_by_payment_id.get(
                payment_id,
                [],
            )
        )

        return [
            self._attempts_by_recovery_id[
                recovery_id
            ]
            for recovery_id in recovery_ids
            if recovery_id
            in self._attempts_by_recovery_id
        ]

    def get_latest_for_payment(
        self,
        payment_id: UUID,
    ) -> RecoveryAttempt | None:
        """
        Return the latest stored recovery attempt
        for a payment.
        """

        attempts = (
            self.get_for_payment(
                payment_id
            )
        )

        if not attempts:
            return None

        return attempts[-1]

    def get_by_status(
        self,
        status: RecoveryStatus,
    ) -> list[RecoveryAttempt]:
        """
        Return all recovery attempts matching a
        lifecycle status.
        """

        return [
            attempt
            for attempt in (
                self._attempts_by_recovery_id.values()
            )
            if attempt.status == status
        ]

    def all_attempts(
        self,
    ) -> list[RecoveryAttempt]:
        """
        Return all stored recovery attempts.
        """

        return list(
            self._attempts_by_recovery_id.values()
        )

    def count(
        self,
    ) -> int:
        """
        Return the number of stored recovery attempts.
        """

        return len(
            self._attempts_by_recovery_id
        )

    def delete(
        self,
        recovery_id: UUID,
    ) -> bool:
        """
        Delete a recovery attempt.

        Returns True when an attempt was deleted and
        False when the recovery ID did not exist.
        """

        attempt = (
            self._attempts_by_recovery_id.pop(
                recovery_id,
                None,
            )
        )

        if attempt is None:
            return False

        recovery_ids = (
            self._recovery_ids_by_payment_id.get(
                attempt.payment_id,
                [],
            )
        )

        if recovery_id in recovery_ids:

            recovery_ids.remove(
                recovery_id
            )

        if not recovery_ids:

            self._recovery_ids_by_payment_id.pop(
                attempt.payment_id,
                None,
            )

        return True

    def clear(
        self,
    ) -> None:
        """
        Clear all stored recovery attempts.

        Primarily useful for tests and simulator resets.
        """

        self._attempts_by_recovery_id.clear()

        self._recovery_ids_by_payment_id.clear()


recovery_attempt_store = (
    RecoveryAttemptStore()
)