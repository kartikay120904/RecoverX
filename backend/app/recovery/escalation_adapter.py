from dataclasses import dataclass

from backend.app.domain.models import Payment

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrationResult,
)

from simulator.recovery.escalation_workflow import (
    EscalationWorkflow,
    EscalationWorkflowResult,
)


@dataclass(frozen=True)
class RecoveryEscalationAdapterResult:
    """
    Result of evaluating escalation after the
    recovery orchestration workflow.
    """

    orchestration: RecoveryOrchestrationResult

    escalation: EscalationWorkflowResult | None


class RecoveryEscalationAdapter:
    """
    Connects recovery orchestration results to
    the escalation workflow.

    This adapter intentionally does not modify
    RecoveryOrchestrator. It provides a separate
    integration boundary.
    """

    def __init__(
        self,
        escalation_workflow: EscalationWorkflow,
    ) -> None:

        self.escalation_workflow = (
            escalation_workflow
        )

    def evaluate(
        self,
        *,
        payment: Payment,
        orchestration: RecoveryOrchestrationResult,
        execution_failures: int = 0,
        max_execution_failures: int = 2,
        high_value_threshold: float | None = None,
    ) -> RecoveryEscalationAdapterResult:
        """
        Evaluate whether the orchestration result
        requires escalation.
        """

        attempt = orchestration.attempt

        retry_limit_reached = (
            "retry limit"
            in orchestration.reason.lower()
        )

        requires_human_approval = (
            orchestration.requires_approval
        )

        has_recovery_action = (
            attempt is not None
        )

        if (
            orchestration.executed
            and not orchestration.blocked
            and not orchestration.requires_approval
        ):

            return RecoveryEscalationAdapterResult(
                orchestration=orchestration,
                escalation=None,
            )

        escalation_result = (
            self.escalation_workflow.evaluate(
                payment=payment,
                attempt=attempt,
                retry_limit_reached=(
                    retry_limit_reached
                ),
                requires_human_approval=(
                    requires_human_approval
                ),
                execution_failures=(
                    execution_failures
                ),
                max_execution_failures=(
                    max_execution_failures
                ),
                high_value_threshold=(
                    high_value_threshold
                ),
            )
        )

        return RecoveryEscalationAdapterResult(
            orchestration=orchestration,
            escalation=escalation_result,
        )