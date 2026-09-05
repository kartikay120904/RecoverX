from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    PAYMENT_CREATED = "payment_created"

    PAYMENT_DETECTED = "payment_detected"

    PAYMENT_FAILED = "payment_failed"

    RECOVERY_PROPOSED = "recovery_proposed"

    RECOVERY_APPROVED = "recovery_approved"

    RECOVERY_SCHEDULED = "recovery_scheduled"

    RECOVERY_ESCALATED = "recovery_escalated"

    ESCALATION_RESOLVED = "escalation_resolved"

    ESCALATION_REJECTED = "escalation_rejected"

    RECOVERY_EXECUTION_STARTED = (
        "recovery_execution_started"
    )

    RECOVERY_SUCCEEDED = (
        "recovery_succeeded"
    )

    RECOVERY_FAILED = (
        "recovery_failed"
    )

    GUARDRAIL_BLOCKED = (
        "guardrail_blocked"
    )

    RETRY_LIMIT_REACHED = (
        "retry_limit_reached"
    )

    INCIDENT_CREATED = (
        "incident_created"
    )


class AuditEvent(BaseModel):
    """
    Immutable record of a significant event
    in the payment recovery lifecycle.
    """

    event_id: UUID = Field(
        default_factory=uuid4
    )

    event_type: AuditEventType

    payment_id: UUID | None = None

    recovery_id: UUID | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )