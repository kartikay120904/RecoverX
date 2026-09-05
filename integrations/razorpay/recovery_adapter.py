from decimal import Decimal

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from integrations.razorpay.client import (
    RazorpayClient,
)

from integrations.razorpay.models import (
    RazorpayExecutionStatus,
    RazorpayRecoveryResult,
)


class RazorpayRecoveryAdapter:
    """
    Executes bounded recovery actions using
    Razorpay Test Mode.

    This adapter does not modify the existing
    recovery simulator.

    The adapter currently supports creating a
    Razorpay Payment Link as a recovery action.
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

    def create_recovery_payment_link(
        self,
        *,
        payment: Payment,
        attempt: RecoveryAttempt,
    ) -> RazorpayRecoveryResult:
        """
        Create a Razorpay Test Mode Payment Link
        representing a real recovery action.

        Razorpay amounts are represented in the
        smallest currency unit.
        """

        amount_in_paise = int(
            (
                payment.amount
                * Decimal("100")
            )
        )

        try:

            response = (
                self.client.client.payment_link.create(
                    {
                        "amount": amount_in_paise,
                        "currency": payment.currency,
                        "reference_id": str(
                            attempt.recovery_id
                        ),
                        "description": (
                            "Recovery payment for "
                            f"payment {payment.payment_id}"
                        ),
                        "notes": {
                            "payment_id": str(
                                payment.payment_id
                            ),
                            "recovery_id": str(
                                attempt.recovery_id
                            ),
                            "strategy": (
                                attempt.strategy.value
                            ),
                        },
                    }
                )
            )

        except Exception as exc:

            return RazorpayRecoveryResult(
                status=(
                    RazorpayExecutionStatus.FAILED
                ),
                amount=Decimal("0"),
                message=(
                    "Failed to create Razorpay "
                    f"recovery payment link: {exc}"
                ),
            )

        return RazorpayRecoveryResult(
            status=(
                RazorpayExecutionStatus
                .REQUIRES_CUSTOMER_ACTION
            ),
            provider_reference_id=response.get(
                "id"
            ),
            recovery_url=response.get(
                "short_url"
            ),
            amount=payment.amount,
            message=(
                "Recovery payment link created. "
                "Customer action is required."
            ),
            raw_status=response.get(
                "status"
            ),
        )