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
class EscalationWorkflowResult:
    """
    Result of evaluating and processing
    a recovery escalation workflow.
    """

    decision: EscalationDecision

    escalation: Escalation | None


class EscalationWorkflow:
    """
    Coordinates escalation policy evaluation
    and escalation creation.

    This workflow intentionally keeps the
    escalation logic isolated from the main
    recovery orchestrator.

    Constructor compatibility is preserved for
    existing callers:

        EscalationWorkflow(
            policy=...,
            service=...,
        )

    and legacy tests:

        EscalationWorkflow(
            escalation_service=...,
            audit_service=...,
        )
    """

    def __init__(
        self,
        policy: EscalationPolicy | None = None,
        service: EscalationService | None = None,
        *,
        escalation_service: EscalationService | None = None,
        audit_service=None,
    ) -> None:
        """
        Create an escalation workflow.

        The workflow accepts both the current
        `policy/service` interface and the legacy
        `escalation_service/audit_service` interface.

        `audit_service` is accepted for backward
        compatibility. EscalationService already owns
        audit behavior.
        """

        resolved_service = (
            service
            or escalation_service
        )

        if resolved_service is None:
            raise ValueError(
                "EscalationWorkflow requires an "
                "EscalationService."
            )

        self.policy = (
            policy
            or EscalationPolicy()
        )

        self.service = resolved_service

        # Compatibility aliases for callers that
        # access the service using the old name.
        self.escalation_service = (
            resolved_service
        )

        # Retain the reference for compatibility,
        # without changing service ownership.
        self.audit_service = audit_service

    def evaluate(
        self,
        *,
        payment: Payment,
        attempt: RecoveryAttempt | None = None,
        retry_limit_reached: bool = False,
        requires_human_approval: bool = False,
        execution_failures: int = 0,
        max_execution_failures: int = 2,
        high_value_threshold: float | None = None,
    ) -> EscalationWorkflowResult:
        """
        Evaluate whether a payment recovery
        should be escalated.

        If escalation is required, create and
        persist an escalation through the
        EscalationService.
        """

        confidence = None

        has_recovery_action = (
            attempt is not None
        )

        if attempt is not None:

            confidence = (
                attempt.predicted_probability
            )

        decision = self.policy.evaluate(
            retry_limit_reached=(
                retry_limit_reached
            ),
            requires_human_approval=(
                requires_human_approval
            ),
            confidence=confidence,
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

        if not decision.should_escalate:

            return EscalationWorkflowResult(
                decision=decision,
                escalation=None,
            )

        escalation = self.service.escalate(
            payment=payment,
            attempt=attempt,
            reason=(
                decision.reason
                or "Recovery requires review."
            ),
        )

        return EscalationWorkflowResult(
            decision=decision,
            escalation=escalation,
        )