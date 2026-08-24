from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment, RecoveryAttempt


class RecoveryEngine:
    """
    Determines whether a failed payment is eligible for recovery
    and proposes a recovery strategy.
    """

    def propose(
        self,
        payment: Payment,
    ) -> RecoveryAttempt | None:
        if payment.status != PaymentStatus.FAILED:
            return None

        strategy = self._select_strategy(payment)
        probability = self._estimate_probability(payment, strategy)

        predicted_revenue = (
            payment.amount * Decimal(str(probability))
        )

        recovery_id = uuid5(
            NAMESPACE_URL,
            f"recoverx-recovery-{payment.payment_id}",
        )

        return RecoveryAttempt(
            recovery_id=recovery_id,
            payment_id=payment.payment_id,
            strategy=strategy,
            predicted_probability=probability,
            predicted_revenue=predicted_revenue,
            status=RecoveryStatus.PROPOSED,
            created_at=payment.created_at,
        )

    def _select_strategy(
        self,
        payment: Payment,
    ) -> RecoveryStrategy:
        failure_code = payment.failure_code

        if failure_code in {
            PaymentFailureCode.BANK_TIMEOUT.value,
            PaymentFailureCode.NETWORK_ERROR.value,
            PaymentFailureCode.GATEWAY_TIMEOUT.value,
        }:
            return RecoveryStrategy.RETRY_PAYMENT

        if failure_code == PaymentFailureCode.INSUFFICIENT_FUNDS.value:
            return RecoveryStrategy.SEND_REMINDER

        if failure_code == PaymentFailureCode.AUTHENTICATION_FAILED.value:
            return RecoveryStrategy.RECOVERY_LINK

        if failure_code == PaymentFailureCode.PAYMENT_DECLINED.value:
            return RecoveryStrategy.RECOVERY_LINK

        return RecoveryStrategy.NO_ACTION

    def _estimate_probability(
        self,
        payment: Payment,
        strategy: RecoveryStrategy,
    ) -> float:
        probabilities = {
            RecoveryStrategy.RETRY_PAYMENT: 0.70,
            RecoveryStrategy.SEND_REMINDER: 0.45,
            RecoveryStrategy.RECOVERY_LINK: 0.55,
            RecoveryStrategy.INCENTIVE: 0.60,
            RecoveryStrategy.ESCALATE: 0.25,
            RecoveryStrategy.NO_ACTION: 0.0,
        }

        return probabilities[strategy]