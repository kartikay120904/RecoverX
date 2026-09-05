from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from backend.app.domain.enums import (
    PaymentFailureCode,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment


@dataclass(frozen=True)
class RecoveryRecommendation:
    # Analytics recommendation fields
    category: str | None = None
    priority: str | None = None
    reason: str | None = None

    # Payment-level recovery recommendation fields
    payment_id: str | None = None
    strategy: str | None = None
    predicted_probability: float | None = None
    predicted_revenue: float | None = None

class RecoveryRecommendations:
    """
    Generates deterministic recovery recommendations
    from payment failures and incident analysis.
    """

    def recommend(
        self,
        *,
        payment: Payment,
        incident,
    ) -> RecoveryRecommendation:
        """
        Generate a recovery recommendation for
        a single payment.
        """

        strategy = self._strategy_for(
            payment=payment,
            incident=incident,
        )

        probability = self._probability_for(
            strategy=strategy,
        )

        predicted_revenue = self._predicted_revenue(
            payment=payment,
            probability=probability,
            strategy=strategy,
        )

        reason = self._reason_for(
            payment=payment,
            incident=incident,
            strategy=strategy,
        )

        return RecoveryRecommendation(
            payment_id=str(
                payment.payment_id
            ),
            strategy=strategy,
            predicted_probability=probability,
            predicted_revenue=predicted_revenue,
            reason=reason,
        )

    def recommend_many(
        self,
        *,
        payments: list[Payment],
        incident,
    ) -> list[RecoveryRecommendation]:
        """
        Generate recommendations only for
        failed payments.
        """

        return [
            self.recommend(
                payment=payment,
                incident=incident,
            )
            for payment in payments
            if payment.failure_code is not None
        ]

    def _strategy_for(
        self,
        *,
        payment: Payment,
        incident,
    ) -> RecoveryStrategy:
        """
        Select the appropriate recovery strategy.
        """

        severity = getattr(
            incident,
            "severity",
            None,
        )

        if severity == "critical":

            return (
                RecoveryStrategy.ESCALATE
            )

        failure_code = (
            payment.failure_code
        )

        if failure_code in {
            PaymentFailureCode.BANK_TIMEOUT.value,
            PaymentFailureCode.NETWORK_ERROR.value,
            PaymentFailureCode.GATEWAY_TIMEOUT.value,
        }:

            return (
                RecoveryStrategy.RETRY_PAYMENT
            )

        if failure_code in {
            PaymentFailureCode.AUTHENTICATION_FAILED.value,
            PaymentFailureCode.INSUFFICIENT_FUNDS.value,
        }:

            return (
                RecoveryStrategy.SEND_REMINDER
            )

        if failure_code == (
            PaymentFailureCode
            .PAYMENT_DECLINED
            .value
        ):

            return (
                RecoveryStrategy.RECOVERY_LINK
            )

        return (
            RecoveryStrategy.NO_ACTION
        )

    def _probability_for(
        self,
        *,
        strategy: RecoveryStrategy,
    ) -> float:
        """
        Return deterministic predicted
        recovery probability.
        """

        probabilities = {
            RecoveryStrategy.RETRY_PAYMENT:
                0.65,

            RecoveryStrategy.SEND_REMINDER:
                0.35,

            RecoveryStrategy.RECOVERY_LINK:
                0.45,

            RecoveryStrategy.ESCALATE:
                0.10,

            RecoveryStrategy.NO_ACTION:
                0.00,
        }

        return probabilities.get(
            strategy,
            0.00,
        )

    def _predicted_revenue(
        self,
        *,
        payment: Payment,
        probability: float,
        strategy: RecoveryStrategy,
    ) -> Decimal:
        """
        Calculate predicted recoverable revenue.
        """

        if strategy == (
            RecoveryStrategy.NO_ACTION
        ):

            return Decimal("0.000")

        return (
            payment.amount
            * Decimal(
                str(probability)
            )
        )

    def _reason_for(
        self,
        *,
        payment: Payment,
        incident,
        strategy: RecoveryStrategy,
    ) -> str:
        """
        Generate a human-readable reason.
        """

        severity = getattr(
            incident,
            "severity",
            "unknown",
        )

        if strategy == (
            RecoveryStrategy.ESCALATE
        ):

            return (
                "Incident severity is critical; "
                "manual escalation is required."
            )

        if strategy == (
            RecoveryStrategy.RETRY_PAYMENT
        ):

            return (
                f"Payment failure code "
                f"'{payment.failure_code}' "
                f"indicates a potentially "
                f"temporary failure suitable "
                f"for retry."
            )

        if strategy == (
            RecoveryStrategy.SEND_REMINDER
        ):

            return (
                f"Payment failure code "
                f"'{payment.failure_code}' "
                f"may require customer action "
                f"or additional funds."
            )

        if strategy == (
            RecoveryStrategy.RECOVERY_LINK
        ):

            return (
                f"Payment failure code "
                f"'{payment.failure_code}' "
                f"is suitable for a recovery "
                f"payment link."
            )

        return (
            f"No deterministic recovery action "
            f"is available for failure code "
            f"'{payment.failure_code}' with "
            f"incident severity '{severity}'."
        )

    def generate(
        self,
        *,
        insights: list,
    ) -> list[RecoveryRecommendation]:

        recommendations = []

        seen_categories = set()

        priority_mapping = {
            "low_recovery_rate": "high",
            "high_failure_rate": "high",
            "high_approval_rate": "medium",
            "high_escalation_rate": "high",
            "best_payment_method": "medium",
            "best_failure_code": "medium",
            "best_strategy": "medium",
        }

        for insight in insights:

            category = insight.category

            if category not in priority_mapping:
                continue

            if category in seen_categories:
                continue

            seen_categories.add(category)

            reason = insight.message

            if not reason:
                reason = (
                    "Recovery insight detected for "
                    f"category '{category}'."
                )

            recommendation = RecoveryRecommendation(
                category=category,
                priority=priority_mapping[category],
                reason=reason,
            )

            recommendations.append(recommendation)

        return recommendations