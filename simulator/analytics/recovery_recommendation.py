from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment
from simulator.analytics.incident_analysis import IncidentAnalysis


@dataclass(frozen=True)
class RecoveryRecommendation:
    payment_id: str
    strategy: RecoveryStrategy
    predicted_probability: float
    predicted_revenue: Decimal
    reason: str


def _strategy_for_failure(
    payment: Payment,
    incident: IncidentAnalysis,
) -> RecoveryStrategy:
    if (
        payment.failure_code
        == PaymentFailureCode.BANK_TIMEOUT.value
    ):
        return RecoveryStrategy.RETRY_PAYMENT

    if (
        payment.failure_code
        == PaymentFailureCode.NETWORK_ERROR.value
    ):
        return RecoveryStrategy.RETRY_PAYMENT

    if (
        payment.failure_code
        == PaymentFailureCode.GATEWAY_TIMEOUT.value
    ):
        return RecoveryStrategy.RETRY_PAYMENT

    if (
        payment.failure_code
        == PaymentFailureCode.AUTHENTICATION_FAILED.value
    ):
        return RecoveryStrategy.SEND_REMINDER

    if (
        payment.failure_code
        == PaymentFailureCode.INSUFFICIENT_FUNDS.value
    ):
        return RecoveryStrategy.SEND_REMINDER

    if (
        payment.failure_code
        == PaymentFailureCode.PAYMENT_DECLINED.value
    ):
        return RecoveryStrategy.RECOVERY_LINK

    if incident.severity == "critical":
        return RecoveryStrategy.ESCALATE

    return RecoveryStrategy.NO_ACTION


def _probability_for_strategy(
    strategy: RecoveryStrategy,
) -> float:
    probabilities = {
        RecoveryStrategy.RETRY_PAYMENT: 0.65,
        RecoveryStrategy.SEND_REMINDER: 0.35,
        RecoveryStrategy.RECOVERY_LINK: 0.45,
        RecoveryStrategy.INCENTIVE: 0.30,
        RecoveryStrategy.ESCALATE: 0.10,
        RecoveryStrategy.NO_ACTION: 0.0,
    }

    return probabilities[strategy]


def recommend_recovery(
    payment: Payment,
    incident: IncidentAnalysis,
) -> RecoveryRecommendation:
    strategy = _strategy_for_failure(
        payment,
        incident,
    )

    probability = _probability_for_strategy(
        strategy,
    )

    predicted_revenue = (
        payment.amount
        * Decimal(str(probability))
    )

    reason = (
        f"Failure code '{payment.failure_code}' "
        f"selected strategy '{strategy.value}' "
        f"with incident severity '{incident.severity}'."
    )

    return RecoveryRecommendation(
        payment_id=str(payment.payment_id),
        strategy=strategy,
        predicted_probability=probability,
        predicted_revenue=predicted_revenue,
        reason=reason,
    )


def recommend_recoveries(
    payments: list[Payment],
    incident: IncidentAnalysis,
) -> list[RecoveryRecommendation]:
    failed_payments = [
        payment
        for payment in payments
        if payment.failure_code is not None
    ]

    return [
        recommend_recovery(
            payment,
            incident,
        )
        for payment in failed_payments
    ]