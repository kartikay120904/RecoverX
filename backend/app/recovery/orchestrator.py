from dataclasses import dataclass
from random import Random
from typing import Any

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
from backend.app.services.recovery_event_service import (
    RecoveryEventService,
)

from simulator.recovery.engine import (
    RecoveryEngine,
)
from simulator.recovery.executor import (
    RecoveryExecutor,
)
from simulator.recovery.guardrails import (
    RecoveryGuardrails,
)
from simulator.recovery.policy import (
    RecoveryPolicyDecision,
    RecoveryPolicyEngine,
)


@dataclass(frozen=True)
class RecoveryOrchestrationResult:
    """
    Complete result of the recovery orchestration workflow.

    Contains:

    - recovery attempt
    - policy decision
    - execution state
    - blocking state
    - approval requirement
    - escalation requirement
    - optional escalation result
    - human-readable reason
    """

    attempt: RecoveryAttempt | None

    policy_decision: RecoveryPolicyDecision | None

    executed: bool

    blocked: bool

    requires_approval: bool

    reason: str

    # Compatibility field used by escalation workflow.
    escalation_required: bool = False

    # Optional result returned by RecoveryEscalationAdapter.
    # Default preserves compatibility with existing callers.
    escalation: Any | None = None


class RecoveryOrchestrator:
    """
    Coordinates the complete RecoverX recovery workflow.

    Flow:

        Payment
            ↓
        RecoveryEngine
            ↓
        Recovery proposal
            ↓
        RecoveryPolicyEngine
            ↓
        Approval / escalation decision
            ↓
        RecoveryGuardrails
            ↓
        RecoveryExecutor
            ↓
        Final recovery result
            ↓
        Recovery lifecycle events
            ↓
        Optional escalation evaluation

    Responsibilities:

    1. Generate a recovery proposal.
    2. Apply business policy.
    3. Stop blocked recoveries.
    4. Surface recoveries requiring approval.
    5. Execute automatically allowed recoveries.
    6. Record lifecycle events.
    7. Optionally evaluate escalation.
    """

    def __init__(
        self,
        engine: RecoveryEngine | None = None,
        policy_engine: RecoveryPolicyEngine | None = None,
        guardrails: RecoveryGuardrails | None = None,
        executor: RecoveryExecutor | None = None,
        event_service: RecoveryEventService | None = None,
        escalation_adapter: Any | None = None,
    ) -> None:

        self.engine = (
            engine
            or RecoveryEngine()
        )

        self.policy_engine = (
            policy_engine
            or RecoveryPolicyEngine()
        )

        self.guardrails = (
            guardrails
            or RecoveryGuardrails()
        )

        self.executor = (
            executor
            or RecoveryExecutor(
                guardrails=self.guardrails
            )
        )

        self.event_service = event_service

        # Escalation is intentionally optional.
        # Existing callers using RecoveryOrchestrator()
        # continue to work unchanged.
        self.escalation_adapter = (
            escalation_adapter
        )

    # =====================================================
    # Public API
    # =====================================================

    def recover(
        self,
        payment: Payment,
        rng: Random,
    ) -> RecoveryOrchestrationResult:
        """
        Execute the complete bounded recovery workflow.

        Steps:

        1. Generate a recovery proposal.
        2. Record the proposal.
        3. Apply recovery policy.
        4. Stop if policy blocks recovery.
        5. Stop if human approval is required.
        6. Execute through the recovery executor.
        7. Record the final execution outcome.
        8. Optionally evaluate escalation.
        """

        # -------------------------------------------------
        # Step 1: Generate recovery proposal
        # -------------------------------------------------

        attempt = self.engine.propose(
            payment
        )

        # -------------------------------------------------
        # Compatibility fallback
        # -------------------------------------------------

        if (
            attempt is None
            and payment.failure_code is not None
        ):

            attempt_data = (
                build_recovery_attempt_data(
                    payment
                )
            )

            attempt = RecoveryAttempt(
                **attempt_data
            )

        # -------------------------------------------------
        # Payment is not eligible for recovery
        # -------------------------------------------------

        if attempt is None:

            self._record_event(
                payment_id=payment.payment_id,
                event_type="recovery_not_eligible",
                details=(
                    "Payment is not eligible "
                    "for recovery."
                ),
            )

            result = (
                RecoveryOrchestrationResult(
                    attempt=None,
                    policy_decision=None,
                    executed=False,
                    blocked=True,
                    requires_approval=False,
                    escalation_required=False,
                    reason=(
                        "Payment is not eligible "
                        "for recovery."
                    ),
                )
            )

            return self._evaluate_escalation(
                payment=payment,
                result=result,
            )

        # -------------------------------------------------
        # Step 2: Record recovery proposal
        # -------------------------------------------------

        self._record_event(
            payment_id=payment.payment_id,
            event_type="recovery_proposed",
            status=attempt.status,
            strategy=attempt.strategy,
            details=(
                "Recovery strategy proposed."
            ),
            metadata={
                "predicted_probability": (
                    attempt.predicted_probability
                ),
                "decision_score": (
                    attempt.decision_score
                ),
            },
        )

        # -------------------------------------------------
        # Step 3: Apply recovery policy
        # -------------------------------------------------

        policy_decision = (
            self.policy_engine.evaluate(
                attempt=attempt,
                payment=payment,
            )
        )

        # -------------------------------------------------
        # Step 4: Policy blocked recovery
        # -------------------------------------------------

        if not policy_decision.allowed:

            self._record_event(
                payment_id=payment.payment_id,
                event_type="recovery_blocked",
                status=attempt.status,
                strategy=attempt.strategy,
                details=policy_decision.reason,
                metadata={
                    "risk_level": (
                        policy_decision.risk_level
                    ),
                    "requires_approval": (
                        policy_decision.requires_approval
                    ),
                },
            )

            result = (
                RecoveryOrchestrationResult(
                    attempt=attempt,
                    policy_decision=policy_decision,
                    executed=False,
                    blocked=True,
                    requires_approval=False,
                    escalation_required=False,
                    reason=policy_decision.reason,
                )
            )

            return self._evaluate_escalation(
                payment=payment,
                result=result,
            )

        # -------------------------------------------------
        # Step 5: Human approval / escalation required
        # -------------------------------------------------

        if policy_decision.requires_approval:

            self._record_event(
                payment_id=payment.payment_id,
                event_type=(
                    "recovery_approval_required"
                ),
                status=attempt.status,
                strategy=attempt.strategy,
                details=policy_decision.reason,
                metadata={
                    "risk_level": (
                        policy_decision.risk_level
                    ),
                    "requires_approval": True,
                    "escalation_required": True,
                },
            )

            result = (
                RecoveryOrchestrationResult(
                    attempt=attempt,
                    policy_decision=policy_decision,
                    executed=False,
                    blocked=False,
                    requires_approval=True,
                    escalation_required=True,
                    reason=policy_decision.reason,
                )
            )

            return self._evaluate_escalation(
                payment=payment,
                result=result,
            )

        # -------------------------------------------------
        # Step 6: Execute bounded recovery
        # -------------------------------------------------

        self._record_event(
            payment_id=payment.payment_id,
            event_type=(
                "recovery_execution_requested"
            ),
            status=attempt.status,
            strategy=attempt.strategy,
            details=(
                "Recovery passed policy and was "
                "submitted for execution."
            ),
        )

        executed_attempt = (
            self.executor.execute(
                attempt=attempt,
                payment=payment,
                rng=rng,
            )
        )

        # -------------------------------------------------
        # Step 7: Determine execution outcome
        # -------------------------------------------------

        executed = (
            executed_attempt.status
            in {
                RecoveryStatus.SUCCEEDED,
                RecoveryStatus.FAILED,
            }
        )

        blocked = not executed

        # -------------------------------------------------
        # Step 8: Record execution result
        # -------------------------------------------------

        if (
            executed_attempt.status
            == RecoveryStatus.SUCCEEDED
        ):

            self._record_event(
                payment_id=payment.payment_id,
                event_type=(
                    "recovery_succeeded"
                ),
                status=(
                    executed_attempt.status
                ),
                strategy=(
                    executed_attempt.strategy
                ),
                details=(
                    "Recovery workflow completed "
                    "successfully."
                ),
                metadata={
                    "actual_revenue": float(
                        executed_attempt.actual_revenue
                        or 0
                    ),
                },
            )

        elif (
            executed_attempt.status
            == RecoveryStatus.FAILED
        ):

            self._record_event(
                payment_id=payment.payment_id,
                event_type=(
                    "recovery_failed"
                ),
                status=(
                    executed_attempt.status
                ),
                strategy=(
                    executed_attempt.strategy
                ),
                details=(
                    "Recovery workflow completed "
                    "but did not recover the payment."
                ),
                metadata={
                    "actual_revenue": float(
                        executed_attempt.actual_revenue
                        or 0
                    ),
                },
            )

        else:

            self._record_event(
                payment_id=payment.payment_id,
                event_type=(
                    "recovery_execution_blocked"
                ),
                status=(
                    executed_attempt.status
                ),
                strategy=(
                    executed_attempt.strategy
                ),
                details=(
                    "Recovery execution was blocked "
                    "before reaching a terminal state."
                ),
            )

        # -------------------------------------------------
        # Step 9: Build orchestration result
        # -------------------------------------------------

        result = (
            RecoveryOrchestrationResult(
                attempt=executed_attempt,
                policy_decision=policy_decision,
                executed=executed,
                blocked=blocked,
                requires_approval=False,
                escalation_required=False,
                reason=(
                    "Recovery workflow completed."
                    if executed
                    else
                    "Recovery execution was blocked "
                    "by guardrails."
                ),
            )
        )

        # -------------------------------------------------
        # Step 10: Evaluate optional escalation
        # -------------------------------------------------

        return self._evaluate_escalation(
            payment=payment,
            result=result,
        )

    # =====================================================
    # Escalation integration
    # =====================================================

    def _evaluate_escalation(
        self,
        *,
        payment: Payment,
        result: RecoveryOrchestrationResult,
    ) -> RecoveryOrchestrationResult:
        """
        Evaluate escalation without affecting recovery.

        Escalation infrastructure is optional and must
        never change or break the underlying recovery
        orchestration workflow.
        """

        if self.escalation_adapter is None:
            return result

        try:

            escalation_result = (
                self.escalation_adapter.evaluate(
                    payment=payment,
                    orchestration=result,
                )
            )

        except Exception:

            # Escalation is an auxiliary workflow.
            #
            # Recovery execution and orchestration must
            # remain functional even if escalation
            # infrastructure is temporarily unavailable.
            return result

        escalation = getattr(
            escalation_result,
            "escalation",
            None,
        )

        escalation_required = (
            result.escalation_required
            or escalation is not None
        )

        return RecoveryOrchestrationResult(
            attempt=result.attempt,
            policy_decision=result.policy_decision,
            executed=result.executed,
            blocked=result.blocked,
            requires_approval=result.requires_approval,
            escalation_required=(
                escalation_required
            ),
            escalation=escalation_result,
            reason=result.reason,
        )

    # =====================================================
    # Internal event recording
    # =====================================================

    def _record_event(
        self,
        *,
        payment_id,
        event_type: str,
        status: RecoveryStatus | None = None,
        strategy=None,
        details: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Record a recovery lifecycle event.

        Event recording is optional so existing callers
        and tests continue working without an event
        service.

        Recovery execution must never fail because
        observability infrastructure is unavailable.
        """

        if self.event_service is None:
            return

        self.event_service.record_event(
            payment_id=payment_id,
            event_type=event_type,
            status=status,
            strategy=strategy,
            details=details,
            metadata=metadata or {},
        )