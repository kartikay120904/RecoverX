from backend.app.recovery.escalation_adapter import (
    RecoveryEscalationAdapter,
)

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
)

from simulator.audit.service import (
    AuditService,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchRunner,
)

from simulator.recovery.escalation import (
    EscalationService,
)
 
from simulator.recovery.escalation_workflow import (
    EscalationWorkflow,
)


class RecoveryBatchFactory:
    """
    Builds the complete RecoverX batch recovery
    workflow using existing components.

    This factory does not modify recovery,
    orchestration, escalation, or execution logic.

    It only composes existing dependencies.
    """

    @staticmethod
    def create(
        *,
        audit_service: AuditService | None = None,
    ) -> RecoveryBatchRunner:
        """
        Create a fully configured batch recovery runner.
        """

        # -------------------------------------------------
        # Step 1: Shared audit service
        # -------------------------------------------------

        if audit_service is None:

            audit_service = AuditService()

        # -------------------------------------------------
        # Step 2: Escalation service
        # -------------------------------------------------

        escalation_service = EscalationService(
            audit_service=audit_service,
        )

        escalation_workflow = EscalationWorkflow(
            escalation_service=escalation_service,
        )
        # -------------------------------------------------
        # Step 5: Recovery → escalation adapter
        # -------------------------------------------------

        escalation_adapter = (
            RecoveryEscalationAdapter(
                escalation_workflow=(
                    escalation_workflow
                ),
            )
        )

        # -------------------------------------------------
        # Step 6: Recovery + escalation coordinator
        # -------------------------------------------------

        coordinator = (
            RecoveryEscalationCoordinator(
                escalation_adapter=(
                    escalation_adapter
                ),
            )
        )

        # -------------------------------------------------
        # Step 7: Batch runner
        # -------------------------------------------------

        return RecoveryBatchRunner(
            coordinator=coordinator,
        )