from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class RazorpayExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REQUIRES_CUSTOMER_ACTION = (
        "requires_customer_action"
    )


class RazorpayRecoveryResult(BaseModel):
    """
    Normalized result returned by the Razorpay
    recovery integration.

    The rest of the recovery system should not
    depend directly on Razorpay SDK response
    structures.
    """

    status: RazorpayExecutionStatus

    provider: str = "razorpay"

    provider_reference_id: str | None = None

    recovery_url: str | None = None

    amount: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    message: str = ""

    raw_status: str | None = None