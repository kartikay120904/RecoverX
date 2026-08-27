from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import Payment
from simulator.analytics.incident_analysis import IncidentAnalysis


@dataclass(frozen=True)
class CounterfactualOption:
    strategy: RecoveryStrategy
    probability: float
    expected_revenue: Decimal
    revenue_uplift: Decimal
    relative_uplift: float
    recommended: bool
    explanation: str


_BASE_PROBABILITIES = {
    RecoveryStrategy.RETRY_PAYMENT: 0.70,
    RecoveryStrategy.SEND_REMINDER: 0.45,
    RecoveryStrategy.RECOVERY_LINK: 0.55,
    RecoveryStrategy.INCENTIVE: 0.60,
    RecoveryStrategy.ESCALATE: 0.25,
    RecoveryStrategy.NO_ACTION: 0.0,
}


def _adjust_probability(
    payment: Payment,
    incident: IncidentAnalysis,
    strategy: RecoveryStrategy,
) -> float:
    probability = _BASE_PROBABILITIES[strategy]

    # Transient failures strongly favor retries.
    if payment.failure_code in {
        "bank_timeout",
        "network_error",
        "gateway_timeout",
    }:
        if strategy == RecoveryStrategy.RETRY_PAYMENT:
            probability += 0.08

        if strategy == RecoveryStrategy.RECOVERY_LINK:
            probability -= 0.05

    # Customer-action failures favor reminders or recovery links.
    if payment.failure_code in {
        "insufficient_funds",
        "authentication_failed",
        "payment_declined",
    }:
        if strategy in {
            RecoveryStrategy.SEND_REMINDER,
            RecoveryStrategy.RECOVERY_LINK,
        }:
            probability += 0.07

        if strategy == RecoveryStrategy.RETRY_PAYMENT:
            probability -= 0.08

    # Critical incidents make immediate automated actions less certain.
    if incident.severity == "critical":
        if strategy == RecoveryStrategy.ESCALATE:
            probability += 0.15
        elif strategy != RecoveryStrategy.NO_ACTION:
            probability -= 0.05

    return max(0.0, min(probability, 0.95))


def _explanation(
    strategy: RecoveryStrategy,
    payment: Payment,
    probability: float,
) -> str:
    failure = payment.failure_code or "unknown"

    if strategy == RecoveryStrategy.RETRY_PAYMENT:
        return (
            f"Retry is evaluated against failure '{failure}'. "
            f"Estimated recovery probability: {probability:.0%}."
        )

    if strategy == RecoveryStrategy.SEND_REMINDER:
        return (
            "Customer follow-up is used when the payment "
            "likely requires customer action."
        )

    if strategy == RecoveryStrategy.RECOVERY_LINK:
        return (
            "A fresh payment/recovery link gives the customer "
            "another path to complete the payment."
        )

    if strategy == RecoveryStrategy.INCENTIVE:
        return (
            "An incentive can increase conversion but should "
            "only be used when the expected revenue justifies it."
        )

    if strategy == RecoveryStrategy.ESCALATE:
        return (
            "Human intervention is preferred when incident "
            "severity makes automated recovery risky."
        )

    return "No automated recovery action is expected to recover revenue."


def simulate_counterfactuals(
    payment: Payment,
    incident: IncidentAnalysis,
) -> list[CounterfactualOption]:

    strategies = [
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStrategy.SEND_REMINDER,
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStrategy.INCENTIVE,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION,
    ]

    raw_results = []

    for strategy in strategies:
        probability = _adjust_probability(
            payment,
            incident,
            strategy,
        )

        expected_revenue = (
            payment.amount * Decimal(str(probability))
        )

        raw_results.append(
            (
                strategy,
                probability,
                expected_revenue,
            )
        )

    best_revenue = max(
        expected_revenue
        for _, _, expected_revenue in raw_results
    )

    options = []

    for strategy, probability, expected_revenue in raw_results:
        uplift = expected_revenue - Decimal("0")

        relative_uplift = (
            float(
                expected_revenue / best_revenue
            )
            if best_revenue > 0
            else 0.0
        )

        options.append(
            CounterfactualOption(
                strategy=strategy,
                probability=round(probability, 4),
                expected_revenue=expected_revenue,
                revenue_uplift=uplift,
                relative_uplift=round(relative_uplift, 4),
                recommended=expected_revenue == best_revenue,
                explanation=_explanation(
                    strategy,
                    payment,
                    probability,
                ),
            )
        )

    return sorted(
        options,
        key=lambda option: option.expected_revenue,
        reverse=True,
    )