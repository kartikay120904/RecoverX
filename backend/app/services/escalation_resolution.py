from dataclasses import dataclass

from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from simulator.recovery.escalation import (
    Escalation,
    EscalationService,
    EscalationStatus,
)


@dataclass(frozen=True)
class EscalationResolutionResult:
    """
    Result of resolving an escalation.

    This bridge keeps escalation resolution
    synchronized with the recovery lifecycle
    without modifying existing services.
    """

    escalation: Escalation

    attempt: RecoveryAttempt | None

    approved: bool

    reason: str


class EscalationResolutionService:
    """
    Connects human escalation decisions with
    recovery attempt lifecycle states.

    Approval flow:

        OPEN
          ↓
        APPROVED
          ↓
        RecoveryAttempt.APPROVED

    Rejection flow:

        OPEN
          ↓
        REJECTED
          ↓
        RecoveryAttempt.REJECTED
    """

    def __init__(
        self,
        escalation_service: EscalationService,
    ) -> None:

        self.escalation_service = (
            escalation_service
        )

    def approve(
        self,
        *,
        escalation_id,
        attempt: RecoveryAttempt | None,
    ) -> EscalationResolutionResult:
        """
        Approve an open escalation and mark the
        associated recovery attempt as approved.
        """

        escalation = (
            self.escalation_service.resolve(
                escalation_id
            )
        )

        if (
            escalation.status
            != EscalationStatus.RESOLVED
        ):
            raise ValueError(
                "Escalation could not be resolved."
            )

        if attempt is not None:

            attempt.status = (
                RecoveryStatus.APPROVED
            )

        return EscalationResolutionResult(
            escalation=escalation,
            attempt=attempt,
            approved=True,
            reason=(
                "Escalation approved and recovery "
                "attempt is ready for scheduling."
            ),
        )

    def reject(
        self,
        *,
        escalation_id,
        attempt: RecoveryAttempt | None,
    ) -> EscalationResolutionResult:
        """
        Reject an escalation and terminate the
        associated recovery attempt.
        """

        escalation = (
            self.escalation_service.reject(
                escalation_id
            )
        )

        if (
            escalation.status
            != EscalationStatus.REJECTED
        ):
            raise ValueError(
                "Escalation could not be rejected."
            )

        if attempt is not None:

            attempt.status = (
                RecoveryStatus.REJECTED
            )

        return EscalationResolutionResult(
            escalation=escalation,
            attempt=attempt,
            approved=False,
            reason=(
                "Escalation rejected and recovery "
                "attempt was rejected."
            ),
        )

    def get_resolution_state(
        self,
        escalation_id,
    ) -> EscalationStatus:
        """
        Return the current escalation status.
        """

        escalation = (
            self.escalation_service.get(
                escalation_id
            )
        )

        if escalation is None:

            raise ValueError(
                "Escalation not found."
            )

        return escalation.status