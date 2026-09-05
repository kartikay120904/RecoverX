from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryAdapter,
)
from integrations.recovery.payment_link_store import (
    payment_link_store,
)


@dataclass(frozen=True)
class RecoveryExecutionResult:
    """
    Normalized result returned by the recovery
    execution integration layer.

    This prevents simulator and domain layers from
    depending directly on Razorpay SDK responses.
    """

    success: bool

    payment_link_id: str | None

    short_url: str | None

    status: str | None

    amount: Decimal

    currency: str

    raw_response: dict[str, Any] | None = None


class RecoveryExecutionAdapter:
    """
    Execution interface for payment recovery.

    Currently delegates recovery execution to the
    Razorpay Payment Link adapter.

    This layer keeps the higher-level recovery
    workflow isolated from Razorpay-specific details.
    """

    def __init__(
        self,
        *,
        payment_link_adapter: (
            PaymentLinkRecoveryAdapter | None
        ) = None,
    ) -> None:

        self.payment_link_adapter = (
            payment_link_adapter
            if payment_link_adapter is not None
            else PaymentLinkRecoveryAdapter()
        )

    def execute(
        self,
        *,
        payment_id: UUID,
        amount: Decimal,
        currency: str = "INR",
        description: str | None = None,
    ) -> RecoveryExecutionResult:
        """
        Execute a recovery action.

        The actual Razorpay operation is delegated to
        PaymentLinkRecoveryAdapter.
        """

        payment_link_result = (
            self.payment_link_adapter
            .create_recovery_link(
                payment_id=payment_id,
                amount=amount,
                currency=currency,
                description=description,
            )
        )

        return RecoveryExecutionResult(
            success=payment_link_result.success,
            payment_link_id=(
                payment_link_result.payment_link_id
            ),
            short_url=(
                payment_link_result.short_url
            ),
            status=(
                payment_link_result.status
            ),
            amount=payment_link_result.amount,
            currency=payment_link_result.currency,
            raw_response=(
                payment_link_result.raw_response
            ),
        )