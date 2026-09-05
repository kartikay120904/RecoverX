from backend.app.recovery.escalation_adapter import (
    RecoveryEscalationAdapter,
)

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrator,
)

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
)

from simulator.recovery.escalation import (
    EscalationService,
)

from simulator.recovery.escalation_policy import (
    EscalationPolicy,
)

from simulator.recovery.escalation_workflow import (
    EscalationWorkflow,
)


def create_recoverx_coordinator() -> (
    RecoveryEscalationCoordinator
):
    """
    Create a fully wired RecoverX coordinator.

    Dependency graph:

        RecoveryOrchestrator
                +
        EscalationPolicy
                +
        EscalationService
                ↓
        EscalationWorkflow
                ↓
        RecoveryEscalationAdapter
                ↓
        RecoveryEscalationCoordinator

    This composition function intentionally
    does not modify any existing recovery,
    escalation, policy, or execution logic.
    """

    orchestrator = (
        RecoveryOrchestrator()
    )

    escalation_policy = (
        EscalationPolicy()
    )

    escalation_service = (
        EscalationService()
    )

    escalation_workflow = (
        EscalationWorkflow(
            policy=escalation_policy,
            service=escalation_service,
        )
    )

    escalation_adapter = (
        RecoveryEscalationAdapter(
            escalation_workflow=(
                escalation_workflow
            )
        )
    )

    return RecoveryEscalationCoordinator(
        orchestrator=orchestrator,
        escalation_adapter=(
            escalation_adapter
        ),
    )