from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from backend.app.services.decision_engine import (
    build_recovery_attempt_data,
)

from backend.app.services.recovery_execution import (
    RecoveryExecutionResult,
    execute_recovery,
)

from backend.app.services.recovery_event_service import (
    RecoveryEventService,
    recovery_event_service,
)

from backend.app.domain.enums import (
    RecoveryStatus,
)


class RecoveryLifecycleService:
    """
    Coordinates the backend recovery lifecycle.

    This service is intentionally additive and does not
    modify existing decision, execution, or event services.

    Flow:

        Payment
            ↓
        Decision Engine
            ↓
        RecoveryAttempt(PROPOSED)
            ↓
        Recovery Execution
            ↓
        Recovery Events
            ↓
        Final RecoveryAttempt
    """

    def __init__(
        self,
        event_service: RecoveryEventService | None = None,
    ) -> None:
        self.event_service = (
            event_service
            or recovery_event_service
        )

    def propose_recovery(
        self,
        payment: Payment,
        incident_severity: str = "normal",
    ) -> RecoveryAttempt:
        """
        Generate a recovery attempt from the existing
        decision engine.

        The attempt begins in PROPOSED state.
        """

        attempt_data = (
            build_recovery_attempt_data(
                payment=payment,
                incident_severity=incident_severity,
            )
        )

        attempt = RecoveryAttempt(
            **attempt_data,
            status=RecoveryStatus.PROPOSED,
        )

        self.event_service.record_event(
            payment_id=payment.payment_id,
            event_type="recovery_proposed",
            strategy=attempt.strategy,
            status=attempt.status,
            details=attempt.reason,
            metadata={
                "predicted_probability": (
                    attempt.predicted_probability
                ),
                "decision_score": (
                    attempt.decision_score
                ),
            },
        )

        return attempt

    def execute_recovery(
        self,
        payment: Payment,
        attempt: RecoveryAttempt,
    ) -> RecoveryExecutionResult:
        """
        Execute an existing recovery attempt using the
        existing recovery execution service.

        Every generated lifecycle event is also stored
        in the RecoveryEventService.
        """

        result = execute_recovery(
            payment=payment,
            attempt=attempt,
        )

        for event in result.events:

            self.event_service.record_event(
                payment_id=event.payment_id,
                event_type=event.event_type,
                strategy=event.strategy,
                status=event.status,
                details=event.details,
                metadata=event.metadata,
            )

        return result

    def recover(
        self,
        payment: Payment,
        incident_severity: str = "normal",
    ) -> RecoveryExecutionResult:
        """
        Execute the complete recovery lifecycle.

        Payment
            ↓
        Decision
            ↓
        PROPOSED
            ↓
        SCHEDULED
            ↓
        EXECUTING
            ↓
        SUCCEEDED / FAILED
        """

        attempt = self.propose_recovery(
            payment=payment,
            incident_severity=incident_severity,
        )

        return self.execute_recovery(
            payment=payment,
            attempt=attempt,
        )

    def get_timeline(
        self,
        payment: Payment,
    ):
        """
        Return the recorded recovery timeline
        for a payment.
        """

        return self.event_service.get_events(
            payment.payment_id,
        )


class RecoveryLifecycleValidator:
    """
    Validates recovery lifecycle state transitions.

    This class is intentionally isolated from the
    existing execution implementation so it can be
    introduced without changing current behavior.
    """

    _ALLOWED_TRANSITIONS: dict[
        RecoveryStatus,
        set[RecoveryStatus],
    ] = {
        RecoveryStatus.PROPOSED: {
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        },
        RecoveryStatus.APPROVED: {
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        },
        RecoveryStatus.REJECTED: set(),
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

    def can_transition(
        self,
        current_status: RecoveryStatus,
        next_status: RecoveryStatus,
    ) -> bool:
        """
        Return whether a lifecycle transition is valid.
        """

        return (
            next_status
            in self._ALLOWED_TRANSITIONS.get(
                current_status,
                set(),
            )
        )

    def validate_transition(
        self,
        current_status: RecoveryStatus,
        next_status: RecoveryStatus,
    ) -> None:
        """
        Validate a transition.

        Raises ValueError when the transition is invalid.
        """

        if not self.can_transition(
            current_status,
            next_status,
        ):
            raise ValueError(
                "Invalid recovery lifecycle transition "
                f"from '{current_status.value}' "
                f"to '{next_status.value}'."
            )

    def allowed_next_statuses(
        self,
        current_status: RecoveryStatus,
    ) -> set[RecoveryStatus]:
        """
        Return all valid next statuses.

        A copy is returned so callers cannot modify
        the internal transition definition.
        """

        return set(
            self._ALLOWED_TRANSITIONS.get(
                current_status,
                set(),
            )
        )


recovery_lifecycle_validator = (
    RecoveryLifecycleValidator()
)