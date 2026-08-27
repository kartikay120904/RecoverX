from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment
from simulator.analytics.incident_analysis import IncidentAnalysis


@dataclass(frozen=True)
class AdaptiveRecoveryDecision:
    payment_id: str
    strategy: RecoveryStrategy
    confidence: float
    priority_score: float
    predicted_probability: float
    predicted_revenue: Decimal
    timing: str
    explanation: str
    signals: list[str]


def _base_probability(strategy: RecoveryStrategy) -> float:
    return {
        RecoveryStrategy.RETRY_PAYMENT: 0.70,
        RecoveryStrategy.SEND_REMINDER: 0.45,
        RecoveryStrategy.RECOVERY_LINK: 0.55,
        RecoveryStrategy.INCENTIVE: 0.60,
        RecoveryStrategy.ESCALATE: 0.25,
        RecoveryStrategy.NO_ACTION: 0.0,
    }[strategy]


def _select_strategy(
    payment: Payment,
    incident: IncidentAnalysis,
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

    if incident.severity == "critical":
        return RecoveryStrategy.ESCALATE

    return RecoveryStrategy.NO_ACTION


def _calculate_confidence(
    payment: Payment,
    incident: IncidentAnalysis,
    strategy: RecoveryStrategy,
) -> float:

    confidence = _base_probability(strategy)

    # Stronger confidence for infrastructure failures because
    # these are usually transient.
    if payment.failure_code in {
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
    }:
        confidence += 0.08

    # Card failures are slightly less predictable.
    if payment.method == PaymentMethod.CARD:
        confidence -= 0.02

    # Critical incidents reduce confidence in automated actions.
    if incident.severity == "critical":
        confidence -= 0.10

    return max(0.0, min(confidence, 0.95))


def _priority_score(
    payment: Payment,
    incident: IncidentAnalysis,
    probability: float,
) -> float:

    score = probability * 100

    # Higher-value payments deserve faster attention.
    if payment.amount >= Decimal("10000"):
        score += 15
    elif payment.amount >= Decimal("5000"):
        score += 10
    elif payment.amount >= Decimal("1000"):
        score += 5

    if incident.severity == "critical":
        score += 15
    elif incident.severity == "warning":
        score += 8

    return round(min(score, 100), 2)


def _timing_for(
    strategy: RecoveryStrategy,
    incident: IncidentAnalysis,
) -> str:

    if strategy == RecoveryStrategy.RETRY_PAYMENT:
        if incident.severity == "critical":
            return "after_incident_stabilizes"
        return "immediately"

    if strategy == RecoveryStrategy.SEND_REMINDER:
        return "within_30_minutes"

    if strategy == RecoveryStrategy.RECOVERY_LINK:
        return "within_15_minutes"

    if strategy == RecoveryStrategy.INCENTIVE:
        return "within_1_hour"

    if strategy == RecoveryStrategy.ESCALATE:
        return "immediately"

    return "no_action"


def _build_signals(
    payment: Payment,
    incident: IncidentAnalysis,
    strategy: RecoveryStrategy,
) -> list[str]:

    signals: list[str] = []

    if payment.failure_code:
        signals.append(
            f"failure_code={payment.failure_code}"
        )

    signals.append(
        f"payment_method={payment.method.value}"
    )

    signals.append(
        f"payment_amount={payment.amount}"
    )

    signals.append(
        f"incident_severity={incident.severity}"
    )

    signals.append(
        f"strategy={strategy.value}"
    )

    return signals


def _build_explanation(
    payment: Payment,
    incident: IncidentAnalysis,
    strategy: RecoveryStrategy,
    probability: float,
    predicted_revenue: Decimal,
) -> str:

    if strategy == RecoveryStrategy.RETRY_PAYMENT:
        reason = (
            "The failure appears transient, so an automated "
            "payment retry has the strongest recovery potential."
        )

    elif strategy == RecoveryStrategy.SEND_REMINDER:
        reason = (
            "The payment appears recoverable through customer "
            "follow-up rather than an immediate technical retry."
        )

    elif strategy == RecoveryStrategy.RECOVERY_LINK:
        reason = (
            "The payment requires customer re-authentication "
            "or another payment attempt."
        )

    elif strategy == RecoveryStrategy.ESCALATE:
        reason = (
            "The incident severity is high enough that automated "
            "recovery should be supplemented by human intervention."
        )

    else:
        reason = (
            "Available signals do not provide enough confidence "
            "for an automated recovery action."
        )

    return (
        f"{reason} "
        f"Estimated recovery probability is "
        f"{probability:.0%}, with expected recoverable revenue "
        f"of ₹{predicted_revenue:.2f}."
    )


def make_adaptive_decision(
    payment: Payment,
    incident: IncidentAnalysis,
) -> AdaptiveRecoveryDecision:

    strategy = _select_strategy(
        payment,
        incident,
    )

    probability = _calculate_confidence(
        payment,
        incident,
        strategy,
    )

    predicted_revenue = (
        payment.amount * Decimal(str(probability))
    )

    priority_score = _priority_score(
        payment,
        incident,
        probability,
    )

    timing = _timing_for(
        strategy,
        incident,
    )

    signals = _build_signals(
        payment,
        incident,
        strategy,
    )

    explanation = _build_explanation(
        payment,
        incident,
        strategy,
        probability,
        predicted_revenue,
    )

    return AdaptiveRecoveryDecision(
        payment_id=str(payment.payment_id),
        strategy=strategy,
        confidence=round(probability, 4),
        priority_score=priority_score,
        predicted_probability=round(probability, 4),
        predicted_revenue=predicted_revenue,
        timing=timing,
        explanation=explanation,
        signals=signals,
    )


def rank_adaptive_recoveries(
    payments: list[Payment],
    incident: IncidentAnalysis,
) -> list[AdaptiveRecoveryDecision]:

    decisions = [
        make_adaptive_decision(
            payment,
            incident,
        )
        for payment in payments
        if payment.failure_code is not None
    ]

    return sorted(
        decisions,
        key=lambda decision: (
            decision.priority_score,
            decision.predicted_revenue,
        ),
        reverse=True,
    )


def decision_to_dict(
    decision: AdaptiveRecoveryDecision,
) -> dict[str, Any]:

    return {
        "payment_id": decision.payment_id,
        "strategy": decision.strategy.value,
        "confidence": decision.confidence,
        "priority_score": decision.priority_score,
        "predicted_probability": decision.predicted_probability,
        "predicted_revenue": str(
            decision.predicted_revenue
        ),
        "timing": decision.timing,
        "explanation": decision.explanation,
        "signals": decision.signals,
    }