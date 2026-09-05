from dataclasses import dataclass
from random import Random

from backend.app.domain.models import Payment

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrationResult,
    RecoveryOrchestrator,
)

from backend.app.recovery.escalation_adapter import (
    RecoveryEscalationAdapter,
    RecoveryEscalationAdapterResult,
)


@dataclass(frozen=True)
class RecoveryEscalationCoordinatorResult:
    """
    Complete result of the recovery and escalation flow.

    Contains:

    - recovery orchestration result
    - optional escalation adapter result
    """

    orchestration: RecoveryOrchestrationResult

    escalation: RecoveryEscalationAdapterResult | None


class RecoveryEscalationCoordinator:
    """
    Coordinates recovery orchestration and escalation evaluation.

    Flow:

        Payment
            ↓
        RecoveryOrchestrator
            ↓
        RecoveryOrchestrationResult
            ↓
        RecoveryEscalationAdapter
            ↓
        EscalationWorkflow
            ↓
        EscalationService

    The coordinator does not change recovery or escalation
    business logic. It only connects existing components.
    """

    def __init__(
        self,
        orchestrator: RecoveryOrchestrator | None = None,
        escalation_adapter: RecoveryEscalationAdapter | None = None,
    ) -> None:

        self.orchestrator = (
            orchestrator
            or RecoveryOrchestrator()
        )

        self.escalation_adapter = (
            escalation_adapter
        )

    def recover(
        self,
        payment: Payment,
        rng: Random,
    ) -> RecoveryEscalationCoordinatorResult:
        """
        Execute recovery orchestration and then evaluate
        whether escalation is required.
        """

        # ---------------------------------------------
        # Step 1: Execute recovery orchestration
        # ---------------------------------------------

        orchestration = (
            self.orchestrator.recover(
                payment=payment,
                rng=rng,
            )
        )

        # ---------------------------------------------
        # Step 2: Evaluate escalation
        #
        # Escalation is optional so existing recovery
        # behavior remains unchanged when no adapter is
        # configured.
        # ---------------------------------------------

        escalation = None

        if self.escalation_adapter is not None:

            escalation = (
                self.escalation_adapter.evaluate(
                    payment=payment,
                    orchestration=orchestration,
                )
            )

        # ---------------------------------------------
        # Step 3: Return combined result
        # ---------------------------------------------

        return RecoveryEscalationCoordinatorResult(
            orchestration=orchestration,
            escalation=escalation,
        )