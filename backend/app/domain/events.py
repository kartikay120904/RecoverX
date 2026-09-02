from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =========================================================
# General Domain Event
# =========================================================


class DomainEvent(BaseModel):

    event_id: UUID = Field(
        default_factory=uuid4
    )

    event_type: str

    entity_id: UUID

    correlation_id: UUID = Field(
        default_factory=uuid4
    )

    actor: str = "system"

    payload: dict[str, Any] = Field(
        default_factory=dict
    )

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )


# =========================================================
# Recovery Event
# =========================================================


class RecoveryEvent(BaseModel):
    """
    Immutable event representing an action or state change
    in the recovery lifecycle.
    """

    event_id: UUID = Field(
        default_factory=uuid4
    )

    payment_id: UUID

    event_type: str

    status: str

    data: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )