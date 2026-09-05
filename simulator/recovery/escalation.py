from enum import Enum
from uuid import UUID, uuid4

from backend.app.domain.audit import AuditEventType
from simulator.audit.service import AuditService


class EscalationStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Escalation:
    """
    Represents a recovery attempt that requires
    explicit human review.
    """

    def __init__(
        self,
        payment_id: UUID,
        recovery_id: UUID | None,
        reason: str,
    ) -> None:
        self.escalation_id = uuid4()

        self.payment_id = payment_id

        self.recovery_id = recovery_id

        self.reason = reason

        self.status = EscalationStatus.OPEN


class EscalationService:
    """
    Handles explicit escalation of payment recovery
    attempts that require human review.
    """

    def __init__(
        self,
        audit_service: AuditService,
    ) -> None:
        self._audit_service = audit_service

        self._escalations: dict[
            UUID,
            Escalation,
        ] = {}

    def escalate(
        self,
        payment,
        attempt=None,
        reason: str = "",
    ) -> Escalation:
        """
        Create an escalation for a payment recovery.
        """

        payment_id = payment.payment_id

        recovery_id = None

        if attempt is not None:
            recovery_id = getattr(
                attempt,
                "recovery_id",
                None,
            )

        escalation = Escalation(
            payment_id=payment_id,
            recovery_id=recovery_id,
            reason=reason,
        )

        self._escalations[
            escalation.escalation_id
        ] = escalation

        self._audit_service.record(
            event_type=(
                AuditEventType.RECOVERY_ESCALATED
            ),
            payment_id=payment_id,
            recovery_id=recovery_id,
            metadata={
                "escalation_id": str(
                    escalation.escalation_id
                ),
                "reason": reason,
            },
        )

        return escalation

    def resolve(
        self,
        escalation_id: UUID,
    ) -> Escalation:
        """
        Mark an escalation as resolved.
        """

        escalation = self._get_escalation(
            escalation_id
        )

        if (
            escalation.status
            != EscalationStatus.OPEN
        ):
            raise ValueError(
                "Only open escalations can "
                "be resolved."
            )

        escalation.status = (
            EscalationStatus.RESOLVED
        )

        self._audit_service.record(
            event_type=(
                AuditEventType.ESCALATION_RESOLVED
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
            },
        )

        return escalation

    def reject(
        self,
        escalation_id: UUID,
    ) -> Escalation:
        """
        Mark an escalation as rejected.
        """

        escalation = self._get_escalation(
            escalation_id
        )

        if (
            escalation.status
            != EscalationStatus.OPEN
        ):
            raise ValueError(
                "Only open escalations can "
                "be rejected."
            )

        escalation.status = (
            EscalationStatus.REJECTED
        )

        self._audit_service.record(
            event_type=(
                AuditEventType.ESCALATION_REJECTED
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
            },
        )

        return escalation

    def get(
        self,
        escalation_id: UUID,
    ) -> Escalation | None:
        """
        Return an escalation by ID.
        """

        return self._escalations.get(
            escalation_id
        )

    def all_escalations(
        self,
    ) -> list[Escalation]:
        """
        Return all escalations.
        """

        return list(
            self._escalations.values()
        )

    def open_escalations(
        self,
    ) -> list[Escalation]:
        """
        Return all escalations awaiting review.
        """

        return [
            escalation
            for escalation in (
                self._escalations.values()
            )
            if escalation.status
            == EscalationStatus.OPEN
        ]

    def _get_escalation(
        self,
        escalation_id: UUID,
    ) -> Escalation:
        """
        Retrieve an escalation or raise an error.
        """

        escalation = self._escalations.get(
            escalation_id
        )

        if escalation is None:
            raise ValueError(
                f"Escalation not found: "
                f"{escalation_id}"
            )

        return escalation