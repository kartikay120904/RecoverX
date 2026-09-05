from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

from integrations.razorpay.client import RazorpayClient


@dataclass(frozen=True)
class PaymentLinkRecoveryResult:
    """
    Result returned after attempting to create a
    Razorpay Payment Link for a recovery workflow.
    """

    success: bool

    payment_link_id: str | None

    short_url: str | None

    status: str | None

    amount: Decimal

    currency: str

    raw_response: dict[str, Any] | None = None


class PaymentLinkRecoveryAdapter:
    """
    Adapter responsible for creating Razorpay Payment
    Links for payment recovery.

    This adapter is intentionally isolated from the
    recovery domain and simulator layers.

    Existing recovery components should not depend on
    Razorpay SDK objects directly.
    """

    def __init__(
        self,
        client: RazorpayClient | None = None,
    ) -> None:

        self.client = (
            client
            if client is not None
            else RazorpayClient()
        )

    def create_recovery_link(
        self,
        *,
        payment_id: UUID,
        amount: Decimal,
        currency: str = "INR",
        description: str | None = None,
    ) -> PaymentLinkRecoveryResult:
        """
        Create a Razorpay Payment Link for recovering
        a failed payment.

        Razorpay expects the amount in the smallest
        currency unit.

        Example:

            ₹500.00 -> 50000 paise
        """

        amount_in_smallest_unit = int(
            amount * Decimal("100")
        )

        payload = {
            "amount": amount_in_smallest_unit,
            "currency": currency,
            "description": (
                description
                or "Payment recovery"
            ),
            "reference_id": str(
                payment_id
            ),
        }

        response = (
            self.client.client.payment_link.create(
                payload
            )
        )

        return PaymentLinkRecoveryResult(
            success=True,
            payment_link_id=response.get(
                "id"
            ),
            short_url=response.get(
                "short_url"
            ),
            status=response.get(
                "status"
            ),
            amount=amount,
            currency=currency,
            raw_response=dict(
                response
            ),
        )