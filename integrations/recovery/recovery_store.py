from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from backend.app.domain.enums import RecoveryStatus
from backend.app.domain.models import (
    RecoveryAttempt,
    RecoveryEvent,
)


@dataclass
class RecoveryStore:
    """
    Lightweight in-memory store for completed
    recovery lifecycle updates.

    This store is intentionally isolated from the
    simulator and existing recovery engine.
    """

    recovery_attempts: dict[
        UUID,
        RecoveryAttempt,
    ] = field(
        default_factory=dict
    )

    recovery_events: list[
        RecoveryEvent
    ] = field(
        default_factory=list
    )

    def register_attempt(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        """
        Register a recovery attempt so its lifecycle
        can later be updated.
        """

        self.recovery_attempts[
            attempt.payment_id
        ] = attempt

    def complete_recovery(
        self,
        *,
        payment_id: UUID,
        actual_revenue: Decimal,
        payment_link_id: str | None = None,
    ) -> RecoveryAttempt | None:
        """
        Mark a registered recovery attempt as
        successfully completed.
        """

        attempt = self.recovery_attempts.get(
            payment_id
        )

        if attempt is None:
            return None

        attempt.actual_revenue = actual_revenue

        attempt.status = (
            RecoveryStatus.SUCCEEDED
        )

        event = RecoveryEvent(
            payment_id=payment_id,
            event_type="recovery.completed",
            status=RecoveryStatus.SUCCEEDED,
            details=(
                "Recovery completed through "
                "Razorpay Payment Link."
            ),
            metadata={
                "payment_link_id": payment_link_id,
                "actual_revenue": str(
                    actual_revenue
                ),
            },
        )

        self.recovery_events.append(
            event
        )

        return attempt

    def get_attempt(
        self,
        payment_id: UUID,
    ) -> RecoveryAttempt | None:
        """
        Return a registered recovery attempt.
        """

        return self.recovery_attempts.get(
            payment_id
        )

    def get_events(
        self,
        payment_id: UUID,
    ) -> list[RecoveryEvent]:
        """
        Return recovery lifecycle events for
        a specific payment.
        """

        return [
            event
            for event in self.recovery_events
            if event.payment_id == payment_id
        ]


# =========================================================
# Shared recovery lifecycle store
# =========================================================

recovery_store = RecoveryStore()