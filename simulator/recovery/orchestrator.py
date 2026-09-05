from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
    RecoveryEvent,
)

from simulator.audit.service import AuditService
from simulator.recovery.engine import RecoveryEngine
from simulator.recovery.escalation import (
    Escalation,
    EscalationService,
)
from simulator.recovery.escalation_policy import (
    EscalationPolicy,
)
from simulator.recovery.lifecycle import RecoveryLifecycle

class RecoveryOrchestrator:
    """
    Coordinates the recovery workflow.

    Responsibilities:

    - Generate recovery proposals
    - Manage lifecycle transitions before execution
    - Create immutable recovery events
    - Maintain an in-memory recovery timeline
    - Evaluate escalation requirements
    - Create human-review escalations

    Important ownership rule:

    RecoveryExecutor owns:

        SCHEDULED
            -> EXECUTING
            -> SUCCEEDED / FAILED

    Therefore, once execution completes, this
    orchestrator records the terminal result without
    attempting another lifecycle transition.
    """

    def __init__(
        self,
        audit_service: AuditService | None = None,
        escalation_policy: EscalationPolicy | None = None,
        escalation_service: EscalationService | None = None,
    ) -> None:

        self.engine = RecoveryEngine()

        self.lifecycle = RecoveryLifecycle()

        self.events: list[RecoveryEvent] = []

        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
        )

        self.escalation_policy = (
            escalation_policy
            if escalation_policy is not None
            else EscalationPolicy()
        )

        self.escalation_service = (
            escalation_service
            if escalation_service is not None
            else EscalationService(
                audit_service=self.audit_service
            )
        )

        self._execution_failures: dict[
            object,
            int,
        ] = {}

    # -------------------------------------------------
    # Recovery proposal
    # -------------------------------------------------

    def propose(
        self,
        payment: Payment,
    ) -> RecoveryAttempt | None:

        attempt = self.engine.propose(
            payment
        )

        if attempt is None:

            self.evaluate_escalation(
                payment=payment,
                attempt=None,
                has_recovery_action=False,
            )

            return None

        self._record_event(
            payment_id=payment.payment_id,
            event_type="recovery_proposed",
            strategy=attempt.strategy,
            status=attempt.status,
            details=attempt.reason,
        )

        return attempt

    # -------------------------------------------------
    # Approval
    # -------------------------------------------------

    def approve(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.approve(
            attempt
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_approved",
            strategy=result.strategy,
            status=result.status,
            details="Recovery proposal approved.",
        )

        return result

    # -------------------------------------------------
    # Rejection
    # -------------------------------------------------

    def reject(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.reject(
            attempt
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_rejected",
            strategy=result.strategy,
            status=result.status,
            details="Recovery proposal rejected.",
        )

        return result

    # -------------------------------------------------
    # Scheduling
    # -------------------------------------------------

    def schedule(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.schedule(
            attempt
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_scheduled",
            strategy=result.strategy,
            status=result.status,
            details="Recovery attempt scheduled.",
        )

        return result

    # -------------------------------------------------
    # Manual execution start
    #
    # This method is retained for direct orchestrator
    # workflows and existing tests.
    #
    # The simulation runner should NOT call this before
    # RecoveryExecutor.execute(), because the executor
    # owns the SCHEDULED -> EXECUTING transition.
    # -------------------------------------------------

    def start_execution(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.start_execution(
            attempt
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_execution_started",
            strategy=result.strategy,
            status=result.status,
            details="Recovery execution started.",
        )

        return result

    # -------------------------------------------------
    # Manual success completion
    #
    # Used for workflows where the orchestrator itself
    # owns the execution lifecycle.
    # -------------------------------------------------

    def mark_succeeded(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.mark_succeeded(
            attempt
        )

        result.actual_revenue = (
            result.predicted_revenue
        )

        self._execution_failures.pop(
            result.payment_id,
            None,
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_succeeded",
            strategy=result.strategy,
            status=result.status,
            details="Recovery completed successfully.",
            metadata={
                "actual_revenue": str(
                    result.actual_revenue
                ),
            },
        )

        return result

    # -------------------------------------------------
    # Manual failure completion
    #
    # Used for workflows where the orchestrator itself
    # owns the execution lifecycle.
    # -------------------------------------------------

    def mark_failed(
        self,
        attempt: RecoveryAttempt,
        payment: Payment | None = None,
    ) -> RecoveryAttempt:

        result = self.lifecycle.mark_failed(
            attempt
        )

        result.actual_revenue = None

        execution_failures = (
            self._execution_failures.get(
                result.payment_id,
                0,
            )
            + 1
        )

        self._execution_failures[
            result.payment_id
        ] = execution_failures

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_failed",
            strategy=result.strategy,
            status=result.status,
            details="Recovery execution failed.",
            metadata={
                "execution_failures": (
                    execution_failures
                ),
            },
        )

        if payment is not None:

            self.evaluate_escalation(
                payment=payment,
                attempt=result,
            )

        return result

    # -------------------------------------------------
    # Terminal execution result
    #
    # Used after RecoveryExecutor.execute().
    #
    # No lifecycle transition happens here because the
    # executor has already transitioned the attempt.
    # -------------------------------------------------

    def record_terminal_result(
        self,
        attempt: RecoveryAttempt,
        *,
        payment: Payment | None = None,
    ) -> RecoveryAttempt:

        if (
            attempt.status
            == RecoveryStatus.SUCCEEDED
        ):

            self._execution_failures.pop(
                attempt.payment_id,
                None,
            )

            self._record_event(
                payment_id=attempt.payment_id,
                event_type="recovery_succeeded",
                strategy=attempt.strategy,
                status=attempt.status,
                details=(
                    "Recovery completed successfully."
                ),
                metadata={
                    "actual_revenue": str(
                        attempt.actual_revenue
                    ),
                },
            )

            return attempt

        if (
            attempt.status
            == RecoveryStatus.FAILED
        ):

            execution_failures = (
                self._execution_failures.get(
                    attempt.payment_id,
                    0,
                )
                + 1
            )

            self._execution_failures[
                attempt.payment_id
            ] = execution_failures

            self._record_event(
                payment_id=attempt.payment_id,
                event_type="recovery_failed",
                strategy=attempt.strategy,
                status=attempt.status,
                details=(
                    "Recovery execution failed."
                ),
                metadata={
                    "execution_failures": (
                        execution_failures
                    ),
                    "actual_revenue": str(
                        attempt.actual_revenue
                    ),
                },
            )

            if payment is not None:

                self.evaluate_escalation(
                    payment=payment,
                    attempt=attempt,
                )

            return attempt

        raise ValueError(
            "Only terminal recovery attempts "
            "can be recorded."
        )

    # -------------------------------------------------
    # Cancellation
    # -------------------------------------------------

    def cancel(
        self,
        attempt: RecoveryAttempt,
    ) -> RecoveryAttempt:

        result = self.lifecycle.cancel(
            attempt
        )

        self._record_event(
            payment_id=result.payment_id,
            event_type="recovery_cancelled",
            strategy=result.strategy,
            status=result.status,
            details="Recovery attempt cancelled.",
        )

        return result

    # -------------------------------------------------
    # Escalation evaluation
    # -------------------------------------------------

    def evaluate_escalation(
        self,
        payment: Payment,
        attempt: RecoveryAttempt | None = None,
        *,
        retry_limit_reached: bool = False,
        requires_human_approval: bool = False,
        confidence: float | None = None,
        minimum_confidence: float = 0.5,
        high_value_threshold: float | None = None,
        max_execution_failures: int = 2,
        has_recovery_action: bool = True,
    ) -> Escalation | None:

        execution_failures = (
            self._execution_failures.get(
                payment.payment_id,
                0,
            )
        )

        payment_amount = getattr(
            payment,
            "amount",
            None,
        )

        decision = (
            self.escalation_policy.evaluate(
                retry_limit_reached=(
                    retry_limit_reached
                ),
                requires_human_approval=(
                    requires_human_approval
                ),
                confidence=confidence,
                minimum_confidence=(
                    minimum_confidence
                ),
                payment_amount=payment_amount,
                high_value_threshold=(
                    high_value_threshold
                ),
                execution_failures=(
                    execution_failures
                ),
                max_execution_failures=(
                    max_execution_failures
                ),
                has_recovery_action=(
                    has_recovery_action
                ),
            )
        )

        if not decision.should_escalate:
            return None

        return self.escalation_service.escalate(
            payment=payment,
            attempt=attempt,
            reason=(
                decision.reason
                or (
                    "Recovery requires "
                    "human review."
                )
            ),
        )

    # -------------------------------------------------
    # Event retrieval
    # -------------------------------------------------

    def get_events(
        self,
        payment_id,
    ) -> list[RecoveryEvent]:

        events = [
            event
            for event in self.events
            if event.payment_id == payment_id
        ]

        events.sort(
            key=lambda event: event.timestamp,
        )

        return [
            event.model_copy(
                deep=True,
            )
            for event in events
        ]

    def get_all_events(
        self,
    ) -> list[RecoveryEvent]:

        events = sorted(
            self.events,
            key=lambda event: event.timestamp,
        )

        return [
            event.model_copy(
                deep=True,
            )
            for event in events
        ]

    # -------------------------------------------------
    # Internal event creation
    # -------------------------------------------------

    def _record_event(
        self,
        payment_id,
        event_type: str,
        strategy,
        status,
        details: str,
        metadata: dict[
            str,
            str | int | float | bool | None,
        ]
        | None = None,
    ) -> RecoveryEvent:

        event = RecoveryEvent(
            payment_id=payment_id,
            event_type=event_type,
            strategy=strategy,
            status=status,
            details=details,
            metadata=metadata or {},
        )

        self.events.append(
            event
        )

        return event