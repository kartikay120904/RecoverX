from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment, RecoveryAttempt


class RecoveryEngine:
    """
    RecoverX 2.0 decision engine.

    Determines whether a failed payment is recoverable,
    selects the most appropriate recovery strategy,
    calculates an explainable decision score,
    and estimates expected recovered revenue.
    """

    BASE_PROBABILITIES = {
        RecoveryStrategy.RETRY_PAYMENT: 0.70,
        RecoveryStrategy.SEND_REMINDER: 0.45,
        RecoveryStrategy.RECOVERY_LINK: 0.55,
        RecoveryStrategy.INCENTIVE: 0.60,
        RecoveryStrategy.ESCALATE: 0.25,
        RecoveryStrategy.NO_ACTION: 0.0,
    }

    def is_recoverable(
        self,
        payment: Payment,
    ) -> bool:
        """
        Determine whether a payment is eligible for recovery.
        """

        return (
            payment.status == PaymentStatus.FAILED
            and payment.failure_code is not None
        )
    def propose(
        self,
        payment: Payment,
    ) -> RecoveryAttempt | None:
        """
        Create a recovery proposal for a failed payment.

        Returns None when the payment is not recoverable.
        """

        if not self.is_recoverable(payment):
            return None

        strategy = self._select_strategy(payment)

        probability = self._estimate_probability(
            payment,
            strategy,
        )

        predicted_revenue = (
            payment.amount * Decimal(str(probability))
        )

        decision_score = self._calculate_decision_score(
            payment,
            strategy,
            probability,
        )

        reason = self._build_reason(
            payment,
            strategy,
            probability,
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
            decision_score=decision_score,
            reason=reason,
            status=RecoveryStatus.PROPOSED,
            created_at=payment.created_at,
        )

    def _select_strategy(
        self,
        payment: Payment,
    ) -> RecoveryStrategy:
        """
        Select the most appropriate recovery strategy.
        """

        # Too many attempts should not continue automatic retries.
        if payment.attempt_number >= 4:
            return RecoveryStrategy.ESCALATE

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
        """
        Return the baseline recovery probability.
        """

        return self.BASE_PROBABILITIES[strategy]

    def _calculate_decision_score(
        self,
        payment: Payment,
        strategy: RecoveryStrategy,
        probability: float,
    ) -> float:
        """
        Calculate an explainable decision confidence score.
        """

        score = probability

        # Repeated attempts reduce confidence.
        if payment.attempt_number > 1:
            score -= min(
                0.05 * (payment.attempt_number - 1),
                0.15,
            )

        # UPI and card payments are stronger candidates
        # for automated recovery.
        if payment.method in {
            PaymentMethod.UPI,
            PaymentMethod.CARD,
        }:
            score += 0.03

        # Transient infrastructure failures are particularly
        # suitable for automated retry.
        if (
            strategy == RecoveryStrategy.RETRY_PAYMENT
            and payment.failure_code
            in {
                PaymentFailureCode.BANK_TIMEOUT.value,
                PaymentFailureCode.NETWORK_ERROR.value,
                PaymentFailureCode.GATEWAY_TIMEOUT.value,
            }
        ):
            score += 0.05

        # Escalation should have lower automation confidence.
        if strategy == RecoveryStrategy.ESCALATE:
            score = min(score, 0.25)

        return round(
            max(0.0, min(1.0, score)),
            4,
        )

    def _build_reason(
        self,
        payment: Payment,
        strategy: RecoveryStrategy,
        probability: float,
    ) -> str:
        """
        Build a human-readable explanation for the decision.
        """

        failure_code = payment.failure_code or "unknown"

        if strategy == RecoveryStrategy.RETRY_PAYMENT:
            explanation = (
                "The failure appears transient, so retrying "
                "the payment is the highest-value recovery action."
            )

        elif strategy == RecoveryStrategy.SEND_REMINDER:
            explanation = (
                "The payment failure indicates insufficient funds, "
                "so a customer reminder is preferred over an immediate retry."
            )

        elif strategy == RecoveryStrategy.RECOVERY_LINK:
            explanation = (
                "The payment requires customer action, so a recovery "
                "link provides a direct path to completing payment."
            )

        elif strategy == RecoveryStrategy.INCENTIVE:
            explanation = (
                "An incentive-based recovery action is appropriate "
                "for this payment context."
            )

        elif strategy == RecoveryStrategy.ESCALATE:
            explanation = (
                "Multiple recovery attempts have already been made, "
                "so the payment should be escalated instead of retried."
            )

        else:
            explanation = (
                "No safe automated recovery action was identified."
            )

        return (
            f"{explanation} "
            f"Failure code: '{failure_code}'. "
            f"Estimated recovery probability: "
            f"{probability:.0%}."
        )