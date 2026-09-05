from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment


class RecoveryStrategyEligibilityService:
    """
    Determines which recovery strategies are eligible
    for a failed payment.

    This service is intentionally isolated from the
    decision engine and does not mutate Payment objects.
    """

    _TRANSIENT_FAILURE_CODES = {
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
    }

    def eligible_strategies(
        self,
        payment: Payment,
    ) -> list[RecoveryStrategy]:
        """
        Return eligible recovery strategies for a payment.
        """

        if (
            payment.status
            not in {
                PaymentStatus.FAILED,
                PaymentStatus.RETRY_ELIGIBLE,
            }
        ):
            return []

        failure_code = self._normalize_failure_code(
            payment.failure_code,
        )

        strategies: list[RecoveryStrategy] = []

        if (
            failure_code
            in self._TRANSIENT_FAILURE_CODES
        ):
            strategies.extend(
                [
                    RecoveryStrategy.RETRY_PAYMENT,
                    RecoveryStrategy.RECOVERY_LINK,
                    RecoveryStrategy.ESCALATE,
                ]
            )

        elif (
            failure_code
            == PaymentFailureCode.INSUFFICIENT_FUNDS.value
        ):
            strategies.extend(
                [
                    RecoveryStrategy.SEND_REMINDER,
                    RecoveryStrategy.RECOVERY_LINK,
                    RecoveryStrategy.ESCALATE,
                ]
            )

        elif (
            failure_code
            == PaymentFailureCode.AUTHENTICATION_FAILED.value
        ):
            strategies.extend(
                [
                    RecoveryStrategy.RECOVERY_LINK,
                    RecoveryStrategy.ESCALATE,
                ]
            )

        elif (
            failure_code
            == PaymentFailureCode.PAYMENT_DECLINED.value
        ):
            strategies.extend(
                [
                    RecoveryStrategy.RECOVERY_LINK,
                    RecoveryStrategy.SEND_REMINDER,
                    RecoveryStrategy.ESCALATE,
                ]
            )

        else:
            strategies.extend(
                [
                    RecoveryStrategy.RETRY_PAYMENT,
                    RecoveryStrategy.SEND_REMINDER,
                    RecoveryStrategy.RECOVERY_LINK,
                    RecoveryStrategy.ESCALATE,
                ]
            )

        return strategies

    def is_strategy_eligible(
        self,
        payment: Payment,
        strategy: RecoveryStrategy,
    ) -> bool:
        """
        Return whether a strategy is eligible
        for the given payment.
        """

        return (
            strategy
            in self.eligible_strategies(
                payment,
            )
        )

    @staticmethod
    def _normalize_failure_code(
        failure_code,
    ) -> str | None:
        """
        Normalize enum and string failure codes.
        """

        if failure_code is None:
            return None

        if hasattr(
            failure_code,
            "value",
        ):
            return str(
                failure_code.value,
            )

        return str(
            failure_code,
        )


recovery_strategy_eligibility_service = (
    RecoveryStrategyEligibilityService()
)