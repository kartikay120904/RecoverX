from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)
from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)

from .enums import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Merchant(BaseModel):
    merchant_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=200)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    created_at: datetime = Field(default_factory=utc_now)


class Customer(BaseModel):
    customer_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID
    email_hash: str
    phone_hash: str
    customer_segment: str = "unknown"
    created_at: datetime = Field(default_factory=utc_now)


class Order(BaseModel):
    order_id: UUID = Field(
        default_factory=uuid4,
    )

    merchant_id: UUID

    customer_id: UUID = Field(
        default_factory=uuid4,
    )

    amount: Decimal = Field(
        gt=0,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    status: OrderStatus = Field(
        default=OrderStatus.CREATED,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )


class Payment(BaseModel):
    """
    Represents a payment attempt.

    order_id and customer_id have default factories so that
    lightweight simulation and decision-engine tests can create
    standalone Payment objects without manually constructing IDs.

    Existing production callers can still explicitly provide both IDs.
    """

    payment_id: UUID = Field(
        default_factory=uuid4,
    )

    order_id: UUID = Field(
        default_factory=uuid4,
    )

    customer_id: UUID = Field(
        default_factory=uuid4,
    )

    amount: Decimal = Field(
        gt=0,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    method: PaymentMethod = PaymentMethod.CARD

    status: PaymentStatus = Field(
        default=PaymentStatus.CREATED,
    )

    failure_code: str | None = Field(
        default=None,
    )

    attempt_number: int = Field(
        default=1,
        ge=1,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
    )

class RecoveryAttempt(BaseModel):
    recovery_id: UUID = Field(
        default_factory=uuid4
    )

    payment_id: UUID = Field(
        default_factory=uuid4
    )

    strategy: RecoveryStrategy

    predicted_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    predicted_revenue: Decimal

    actual_revenue: Decimal | None = None

    status: RecoveryStatus = (
        RecoveryStatus.PROPOSED
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(
            timezone.utc
        )
    )

    # Compatibility fields used by backend/orchestrator
    reason: str = ""

    decision_score: float = 0.0

    @field_validator(
        "strategy",
        mode="before",
    )
    @classmethod
    def normalize_strategy(
        cls,
        value,
    ):
        if value == "retry":
            return "retry_payment"

        return value


class RecoveryEvent(BaseModel):
    """
    Represents an immutable event in the recovery lifecycle.

    Events are used to build an operational audit trail and
    recovery timeline for each payment.
    """

    event_id: UUID = Field(
        default_factory=uuid4,
    )

    payment_id: UUID

    event_type: str = Field(
        min_length=1,
        max_length=100,
    )

    timestamp: datetime = Field(
        default_factory=utc_now,
    )

    strategy: RecoveryStrategy | None = None

    status: RecoveryStatus | None = None

    details: str | None = Field(
        default=None,
        max_length=500,
    )

    metadata: dict[
        str,
        str | int | float | bool | None
    ] = Field(
        default_factory=dict,
    )
