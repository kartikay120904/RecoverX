from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import Payment
from simulator.recovery.engine import RecoveryEngine


@dataclass(frozen=True)
class RecoveryExperimentResult:
    strategy: RecoveryStrategy
    probability: float
    expected_revenue: Decimal
    recommendation: str


def compare_recovery_strategies(
    payment: Payment,
) -> list[RecoveryExperimentResult]:
    """
    Compare every available recovery strategy for a failed payment.

    This is a decision-support simulation only. It does not execute
    any payment or modify the supplied payment.
    """

    if payment.amount <= 0:
        return []

    engine = RecoveryEngine()

    strategies = [
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStrategy.SEND_REMINDER,
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStrategy.INCENTIVE,
        RecoveryStrategy.ESCALATE,
        RecoveryStrategy.NO_ACTION,
    ]

    results: list[RecoveryExperimentResult] = []

    for strategy in strategies:
        probability = engine.BASE_PROBABILITIES[strategy]

        # Penalize repeated attempts consistently with the decision engine.
        if payment.attempt_number > 1:
            probability -= min(
                0.05 * (payment.attempt_number - 1),
                0.15,
            )

        probability = max(0.0, min(1.0, probability))

        expected_revenue = (
            payment.amount * Decimal(str(probability))
        )

        results.append(
            RecoveryExperimentResult(
                strategy=strategy,
                probability=round(probability, 4),
                expected_revenue=expected_revenue,
                recommendation="candidate",
            )
        )

    results.sort(
        key=lambda result: result.expected_revenue,
        reverse=True,
    )

    if results:
        best_strategy = results[0].strategy

        results = [
            RecoveryExperimentResult(
                strategy=result.strategy,
                probability=result.probability,
                expected_revenue=result.expected_revenue,
                recommendation=(
                    "recommended"
                    if result.strategy == best_strategy
                    else "alternative"
                ),
            )
            for result in results
        ]

    return results