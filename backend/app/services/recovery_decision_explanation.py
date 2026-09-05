from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStrategy,
)
from backend.app.services.decision_engine import (
    StrategyDecision,
)


@dataclass(frozen=True)
class RecoveryDecisionExplanation:
    """
    Structured explanation for a recovery decision.

    This component is intentionally read-only and does
    not modify the decision engine or payment objects.
    """

    strategy: RecoveryStrategy

    confidence: float

    expected_revenue: Decimal

    priority: str

    explanation: str

    signals: list[str]


class RecoveryDecisionExplanationService:
    """
    Converts a StrategyDecision into a structured,
    human-readable recovery explanation.
    """

    def explain(
        self,
        decision: StrategyDecision,
    ) -> RecoveryDecisionExplanation:
        """
        Build a structured explanation for a recovery
        decision.
        """

        confidence = (
            self._confidence(
                decision.predicted_probability,
            )
        )

        priority = (
            self._priority(
                decision.decision_score,
            )
        )

        signals = (
            self._build_signals(
                decision,
            )
        )

        explanation = (
            self._build_explanation(
                decision,
                confidence,
                priority,
            )
        )

        return RecoveryDecisionExplanation(
            strategy=decision.strategy,
            confidence=decision.predicted_probability,
            expected_revenue=(
                decision.predicted_revenue
            ),
            priority=priority,
            explanation=explanation,
            signals=signals,
        )

    @staticmethod
    def _confidence(
        probability: float,
    ) -> str:
        """
        Convert probability into a confidence label.
        """

        if probability >= 0.80:
            return "high"

        if probability >= 0.50:
            return "medium"

        return "low"

    @staticmethod
    def _priority(
        decision_score: float,
    ) -> str:
        """
        Convert decision score into a priority level.
        """

        if decision_score >= 0.80:
            return "high"

        if decision_score >= 0.50:
            return "medium"

        return "low"

    @staticmethod
    def _build_signals(
        decision: StrategyDecision,
    ) -> list[str]:
        """
        Build machine-readable explanation signals.
        """

        signals = [
            f"strategy:{decision.strategy.value}",
            (
                "probability:"
                f"{decision.predicted_probability:.2f}"
            ),
            (
                "decision_score:"
                f"{decision.decision_score:.4f}"
            ),
        ]

        if (
            decision.predicted_revenue
            > Decimal("0")
        ):
            signals.append(
                "positive_expected_revenue"
            )

        return signals

    @staticmethod
    def _build_explanation(
        decision: StrategyDecision,
        confidence: str,
        priority: str,
    ) -> str:
        """
        Build a concise human-readable explanation.
        """

        return (
            f"Selected strategy "
            f"'{decision.strategy.value}' "
            f"with {confidence} recovery confidence "
            f"and {priority} execution priority. "
            f"{decision.reason}"
        )


recovery_decision_explanation_service = (
    RecoveryDecisionExplanationService()
)