from dataclasses import dataclass
from uuid import UUID

from backend.app.domain.audit import (
    AuditEventType,
)

from simulator.audit.service import (
    AuditService,
)

from simulator.recovery.escalation import (
    Escalation,
    EscalationService,
    EscalationStatus,
)


@dataclass(frozen=True)
class EscalationResolutionResult:
    """
    Result of resolving or rejecting
    an escalation.
    """

    escalation: Escalation

    approved: bool

    reason: str


class EscalationResolutionWorkflow:
    """
    Handles the human decision stage of
    the escalation lifecycle.

    OPEN
        ->
    RESOLVED / REJECTED

    The workflow remains isolated from the
    recovery orchestrator and execution layer.
    """

    def __init__(
        self,
        escalation_service: EscalationService,
        audit_service: AuditService,
    ) -> None:

        self.escalation_service = (
            escalation_service
        )

        self.audit_service = (
            audit_service
        )

    def approve(
        self,
        escalation_id: UUID,
        reason: str = (
            "Escalation approved for recovery."
        ),
    ) -> EscalationResolutionResult:
        """
        Approve an open escalation.
        """

        escalation = (
            self.escalation_service.get(
                escalation_id
            )
        )

        if escalation is None:

            raise ValueError(
                f"Escalation not found: "
                f"{escalation_id}"
            )

        if (
            escalation.status
            != EscalationStatus.OPEN
        ):

            raise ValueError(
                "Only open escalations "
                "can be approved."
            )

        escalation = (
            self.escalation_service.resolve(
                escalation_id
            )
        )

        self.audit_service.record(
            event_type=(
                AuditEventType.RECOVERY_APPROVED
            ),
            payment_id=(
                escalation.payment_id
            ),
            recovery_id=(
                escalation.recovery_id
            ),
            metadata={
                "escalation_id": str(
                    escalation.escalation_id
                ),
                "reason": reason,
            },
        )

        return EscalationResolutionResult(
            escalation=escalation,
            approved=True,
            reason=reason,
        )

    def reject(
        self,
        escalation_id: UUID,
        reason: str = (
            "Escalation rejected."
        ),
    ) -> EscalationResolutionResult:
        """
        Reject an open escalation.
        """

        escalation = (
            self.escalation_service.get(
                escalation_id
            )
        )

        if escalation is None:

            raise ValueError(
                f"Escalation not found: "
                f"{escalation_id}"
            )

        if (
            escalation.status
            != EscalationStatus.OPEN
        ):

            raise ValueError(
                "Only open escalations "
                "can be rejected."
            )

        escalation = (
            self.escalation_service.reject(
                escalation_id
            )
        )

        self.audit_service.record(
            event_type=(
                AuditEventType.RECOVERY_FAILED
            ),
            payment_id=(
                escalation.payment_id
            ),
            recovery_id=(
                escalation.recovery_id
            ),
            metadata={
                "escalation_id": str(
                    escalation.escalation_id
                ),
                "reason": reason,
            },
        )

        return EscalationResolutionResult(
            escalation=escalation,
            approved=False,
            reason=reason,
        )