from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import (
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
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
    order_id: UUID = Field(default_factory=uuid4)
    merchant_id: UUID
    customer_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)


class Payment(BaseModel):
    payment_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    customer_id: UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    method: PaymentMethod
    status: PaymentStatus = PaymentStatus.CREATED
    failure_code: str | None = None
    attempt_number: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class RecoveryAttempt(BaseModel):
    recovery_id: UUID = Field(default_factory=uuid4)
    payment_id: UUID
    strategy: RecoveryStrategy

    predicted_probability: float = Field(ge=0, le=1)
    predicted_revenue: Decimal = Field(ge=0)

    actual_revenue: Decimal | None = Field(default=None, ge=0)

    # RecoverX 2.0 decision intelligence
    decision_score: float = Field(default=0.0, ge=0, le=1)
    reason: str = Field(default="Recovery strategy selected from payment failure context.")

    status: RecoveryStatus = RecoveryStatus.PROPOSED
    created_at: datetime = Field(default_factory=utc_now)