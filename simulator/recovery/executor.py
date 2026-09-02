from decimal import Decimal
from random import Random

from backend.app.domain.enums import RecoveryStatus
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)
from backend.app.domain.state_machine import (
    transition_recovery,
)
from backend.app.services.recovery_event_service import (
    recovery_event_service,
)


class RecoveryExecutor:
    """
    Executes a recovery attempt and records an immutable
    recovery audit trail.
    """

    def execute(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
        rng: Random,
    ) -> RecoveryAttempt:

        if attempt.status not in {
            RecoveryStatus.PROPOSED,
            RecoveryStatus.APPROVED,
        }:
            raise ValueError(
                "Only proposed recovery attempts can be executed"
            )

        # -------------------------------------------------
        # Start execution
        # -------------------------------------------------

        transition_recovery(
            attempt,
            RecoveryStatus.EXECUTING,
        )

        recovery_event_service.record_event(
            payment_id=payment.payment_id,
            event_type="recovery.execution_started",
            status=RecoveryStatus.EXECUTING,
            strategy=attempt.strategy,
            details="Recovery attempt execution started.",
            metadata={
                "recovery_id": str(
                    attempt.recovery_id
                ),
                "predicted_probability": (
                    attempt.predicted_probability
                ),
                "decision_score": (
                    attempt.decision_score
                ),
            },
        )

        # -------------------------------------------------
        # Simulate recovery result
        # -------------------------------------------------

        success = (
            rng.random()
            < attempt.predicted_probability
        )

        # -------------------------------------------------
        # Recovery succeeded
        # -------------------------------------------------

        if success:

            transition_recovery(
                attempt,
                RecoveryStatus.SUCCEEDED,
            )

            attempt.actual_revenue = (
                payment.amount
            )

            recovery_event_service.record_event(
                payment_id=payment.payment_id,
                event_type="recovery.succeeded",
                status=RecoveryStatus.SUCCEEDED,
                strategy=attempt.strategy,
                details=(
                    "Recovery attempt completed "
                    "successfully."
                ),
                metadata={
                    "recovery_id": str(
                        attempt.recovery_id
                    ),
                    "actual_revenue": str(
                        attempt.actual_revenue
                    ),
                },
            )

        # -------------------------------------------------
        # Recovery failed
        # -------------------------------------------------

        else:

            transition_recovery(
                attempt,
                RecoveryStatus.FAILED,
            )

            attempt.actual_revenue = Decimal("0")

            recovery_event_service.record_event(
                payment_id=payment.payment_id,
                event_type="recovery.failed",
                status=RecoveryStatus.FAILED,
                strategy=attempt.strategy,
                details=(
                    "Recovery attempt completed "
                    "without recovering payment revenue."
                ),
                metadata={
                    "recovery_id": str(
                        attempt.recovery_id
                    ),
                    "actual_revenue": "0",
                },
            )

        return attempt
