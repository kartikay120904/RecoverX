from integrations.execution.interface import (
    RecoveryExecutionInterface,
    RecoveryExecutionRequest,
    RecoveryExecutionResult,
)

from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryAdapter,
)


class RazorpayPaymentLinkExecutionAdapter(
    RecoveryExecutionInterface,
):
    """
    Executes recovery actions by creating a
    Razorpay Payment Link.

    This adapter converts the generic RecoverX
    execution contract into a Razorpay-specific
    payment link request.
    """

    def __init__(
        self,
        *,
        payment_link_adapter: (
            PaymentLinkRecoveryAdapter | None
        ) = None,
    ) -> None:

        self._payment_link_adapter = (
            payment_link_adapter
            if payment_link_adapter is not None
            else PaymentLinkRecoveryAdapter()
        )

    def execute(
        self,
        *,
        request: RecoveryExecutionRequest,
    ) -> RecoveryExecutionResult:
        """
        Create a Razorpay Payment Link for the
        requested recovery action.
        """

        try:

            result = (
                self._payment_link_adapter
                .create_recovery_link(
                    payment_id=request.payment_id,
                    amount=request.amount,
                    currency=request.currency,
                    description=request.description,
                )
            )

            return RecoveryExecutionResult(
                success=result.success,
                execution_id=result.payment_link_id,
                status=(
                    result.status
                    or "unknown"
                ),
                recovery_url=result.short_url,
                provider="razorpay",
            )

        except Exception as exc:

            return RecoveryExecutionResult(
                success=False,
                execution_id=None,
                status="failed",
                recovery_url=None,
                provider="razorpay",
                error=str(exc),
            )