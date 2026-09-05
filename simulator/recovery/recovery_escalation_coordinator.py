from dataclasses import dataclass

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.recovery.escalation import (
    Escalation,
)
from simulator.recovery.escalation_manager import (
    EscalationManager,
    EscalationManagerResult,
)


@dataclass(frozen=True)
class RecoveryEscalationResult:
    """
    Result of evaluating whether a recovery
    workflow should be escalated.
    """

    manager_result: EscalationManagerResult

    escalation: Escalation | None


class RecoveryEscalationCoordinator:
    """
    Converts recovery workflow signals into
    escalation workflow decisions.

    This layer intentionally does not execute
    recovery operations. It only coordinates
    escalation evaluation.
    """

    def __init__(
        self,
        escalation_manager: EscalationManager,
    ) -> None:

        self._escalation_manager = (
            escalation_manager
        )

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
    ) -> RecoveryEscalationResult:
        """
        Evaluate recovery escalation signals.
        """

        manager_result = (
            self._escalation_manager.evaluate(
                payment=payment,
                attempt=attempt,
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

        return RecoveryEscalationResult(
            manager_result=manager_result,
            escalation=(
                manager_result.escalation
            ),
        )