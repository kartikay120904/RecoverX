from dataclasses import dataclass

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


@dataclass(frozen=True)
class EscalationManagerResult:
    """
    Result of evaluating and optionally
    creating a recovery escalation.
    """

    decision: EscalationDecision

    escalation: Escalation | None


class EscalationManager:
    """
    Coordinates escalation policy evaluation
    and escalation creation.

    This class keeps policy decisions separate
    from persistence and audit behavior.
    """

    def __init__(
        self,
        policy: EscalationPolicy,
        service: EscalationService,
    ) -> None:

        self._policy = policy

        self._service = service

    def evaluate(
        self,
        *,
        payment: Payment,
        attempt: RecoveryAttempt | None = None,
        retry_limit_reached: bool = False,
        requires_human_approval: bool = False,
        confidence: float | None = None,
        minimum_confidence: float = 0.5,
        high_value_threshold: float | None = None,
        execution_failures: int = 0,
        max_execution_failures: int = 2,
        has_recovery_action: bool = True,
    ) -> EscalationManagerResult:
        """
        Evaluate escalation requirements and
        create an escalation when necessary.
        """

        decision = (
            self._policy.evaluate(
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
                payment_amount=float(
                    payment.amount
                ),
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

            return EscalationManagerResult(
                decision=decision,
                escalation=None,
            )

        escalation = (
            self._service.escalate(
                payment=payment,
                attempt=attempt,
                reason=(
                    decision.reason
                    or "Recovery requires review."
                ),
            )
        )

        return EscalationManagerResult(
            decision=decision,
            escalation=escalation,
        )