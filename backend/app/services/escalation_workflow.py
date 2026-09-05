from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)
from simulator.recovery.escalation import (
    Escalation,
    EscalationService,
)
from simulator.recovery.escalation_policy import (
    EscalationDecision,
    EscalationPolicy,
)
from simulator.recovery.policy import (
    RecoveryPolicyDecision,
)


@dataclass(frozen=True)
class EscalationWorkflowResult:
    """
    Complete result of escalation evaluation.

    This service connects recovery policy decisions
    with the escalation policy and escalation service
    without modifying the existing recovery workflow.
    """

    should_escalate: bool

    escalation: Escalation | None

    decision: EscalationDecision

    reason: str | None


class EscalationWorkflowService:
    """
    Coordinates escalation evaluation and creation.

    Flow:

        Payment
          ↓
        Recovery Attempt
          ↓
        Recovery Policy Decision
          ↓
        Escalation Policy
          ↓
        Escalation Service
          ↓
        Open Escalation
    """

    def __init__(
        self,
        escalation_policy: (
            EscalationPolicy | None
        ) = None,
        escalation_service: (
            EscalationService | None
        ) = None,
    ) -> None:

        self.escalation_policy = (
            escalation_policy
            or EscalationPolicy()
        )

        if escalation_service is None:
            raise ValueError(
                "An EscalationService instance "
                "is required."
            )

        self.escalation_service = (
            escalation_service
        )

    def evaluate_and_escalate(
        self,
        *,
        payment: Payment,
        attempt: RecoveryAttempt | None,
        recovery_policy_decision: (
            RecoveryPolicyDecision | None
        ) = None,
        retry_limit_reached: bool = False,
        execution_failures: int = 0,
        has_recovery_action: bool = True,
        minimum_confidence: float = 0.5,
        high_value_threshold: (
            Decimal | None
        ) = None,
    ) -> EscalationWorkflowResult:
        """
        Evaluate escalation conditions and create
        an escalation when required.
        """

        requires_human_approval = (
            recovery_policy_decision
            is not None
            and recovery_policy_decision
            .requires_approval
        )

        confidence = None

        if attempt is not None:
            confidence = (
                attempt
                .predicted_probability
            )

        payment_amount = float(
            payment.amount
        )

        threshold = None

        if high_value_threshold is not None:
            threshold = float(
                high_value_threshold
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
                payment_amount=(
                    payment_amount
                ),
                high_value_threshold=(
                    threshold
                ),
                execution_failures=(
                    execution_failures
                ),
                has_recovery_action=(
                    has_recovery_action
                ),
            )
        )

        if not decision.should_escalate:

            return EscalationWorkflowResult(
                should_escalate=False,
                escalation=None,
                decision=decision,
                reason=decision.reason,
            )

        escalation = (
            self.escalation_service
            .escalate(
                payment=payment,
                attempt=attempt,
                reason=(
                    decision.reason
                    or "Recovery requires "
                    "human review."
                ),
            )
        )

        return EscalationWorkflowResult(
            should_escalate=True,
            escalation=escalation,
            decision=decision,
            reason=decision.reason,
        )