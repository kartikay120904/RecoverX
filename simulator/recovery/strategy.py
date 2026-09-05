from dataclasses import dataclass

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import Payment

from simulator.recovery.diagnosis import FailureDiagnosis


# =========================================================
# Strategy Score
# =========================================================


@dataclass(frozen=True)
class StrategyScore:
    """
    Represents the score assigned to a possible
    recovery strategy.
    """

    strategy: RecoveryStrategy

    score: float

    reason: str


# =========================================================
# Recovery Decision
# =========================================================


@dataclass(frozen=True)
class RecoveryDecision:
    """
    Final recovery decision produced by the
    strategy intelligence layer.
    """

    strategy: RecoveryStrategy

    score: float

    reason: str

    diagnosis: FailureDiagnosis

    alternatives: list[StrategyScore]


# =========================================================
# Recovery Strategy Engine
# =========================================================


class RecoveryStrategyEngine:
    """
    Evaluates possible recovery strategies and
    selects the most appropriate intervention.

    Decision flow:

        Failed Payment
              ↓
        Root Cause Diagnosis
              ↓
        Strategy Scoring
              ↓
        Attempt Penalties
              ↓
        Best Strategy
    """

    def decide(
        self,
        payment: Payment,
        diagnosis: FailureDiagnosis,
    ) -> RecoveryDecision:
        """
        Evaluate all recovery strategies and return
        the highest scoring decision.
        """

        scores = self._score_strategies(
            payment,
            diagnosis,
        )

        ranked = sorted(
            scores,
            key=lambda item: item.score,
            reverse=True,
        )

        best = ranked[0]

        return RecoveryDecision(
            strategy=best.strategy,
            score=best.score,
            reason=best.reason,
            diagnosis=diagnosis,
            alternatives=ranked,
        )

    # =====================================================
    # Strategy Scoring
    # =====================================================

    def _score_strategies(
        self,
        payment: Payment,
        diagnosis: FailureDiagnosis,
    ) -> list[StrategyScore]:
        """
        Score every available recovery strategy.

        Root-cause intelligence is applied first.

        Retry penalties are applied last so safety
        constraints cannot be overridden by category
        scoring.
        """

        strategy_scores: dict[
            RecoveryStrategy,
            float,
        ] = {
            RecoveryStrategy.RETRY_PAYMENT: 0.10,
            RecoveryStrategy.SEND_REMINDER: 0.10,
            RecoveryStrategy.RECOVERY_LINK: 0.10,
            RecoveryStrategy.INCENTIVE: 0.10,
            RecoveryStrategy.ESCALATE: 0.05,
            RecoveryStrategy.NO_ACTION: 0.01,
        }

        # -------------------------------------------------
        # Apply diagnosis recommendation
        # -------------------------------------------------

        recommended = (
            diagnosis.recommended_strategy
        )

        strategy_scores[recommended] = max(
            strategy_scores[recommended],
            diagnosis.confidence,
        )

        # -------------------------------------------------
        # Apply root-cause intelligence FIRST
        # -------------------------------------------------

        self._apply_failure_category_scores(
            diagnosis,
            strategy_scores,
        )

        # -------------------------------------------------
        # Apply retry penalties LAST
        #
        # This is intentionally after category scoring.
        # Otherwise a BANK_TIMEOUT category could reset
        # the retry score back to 0.90.
        # -------------------------------------------------

        self._apply_attempt_penalty(
            payment,
            strategy_scores,
        )

        # -------------------------------------------------
        # Convert scores to StrategyScore objects
        # -------------------------------------------------

        return [
            StrategyScore(
                strategy=strategy,
                score=max(
                    0.0,
                    min(
                        round(
                            score,
                            4,
                        ),
                        1.0,
                    ),
                ),
                reason=self._build_reason(
                    strategy,
                    diagnosis,
                    score,
                ),
            )
            for strategy, score in (
                strategy_scores.items()
            )
        ]

    # =====================================================
    # Attempt Penalties
    # =====================================================

    def _apply_attempt_penalty(
        self,
        payment: Payment,
        scores: dict[
            RecoveryStrategy,
            float,
        ],
    ) -> None:
        """
        Reduce retry preference as the number of
        payment attempts increases.

        This prevents the decision engine from
        repeatedly selecting automatic retries.
        """

        attempt_number = (
            payment.attempt_number
        )

        # Second attempt:
        # Retry remains possible but confidence
        # is reduced.

        if attempt_number >= 2:

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] *= 0.70

        # Third attempt:
        # Retry confidence is significantly reduced
        # and escalation becomes more attractive.

        if attempt_number >= 3:

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] *= 0.40

            scores[
                RecoveryStrategy.ESCALATE
            ] = max(
                scores[
                    RecoveryStrategy.ESCALATE
                ],
                0.60,
            )

        # Fourth or later attempt:
        # Automatic retry should effectively stop.

        if attempt_number >= 4:

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] = 0.0

            scores[
                RecoveryStrategy.ESCALATE
            ] = max(
                scores[
                    RecoveryStrategy.ESCALATE
                ],
                0.85,
            )

    # =====================================================
    # Root Cause Intelligence
    # =====================================================

    def _apply_failure_category_scores(
        self,
        diagnosis: FailureDiagnosis,
        scores: dict[
            RecoveryStrategy,
            float,
        ],
    ) -> None:
        """
        Adjust strategy scores based on the
        diagnosed root cause.
        """

        category = diagnosis.category

        # -------------------------------------------------
        # Temporary infrastructure failures
        # -------------------------------------------------

        if category in {
            "temporary_bank_failure",
            "temporary_gateway_failure",
            "network_failure",
        }:

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] = max(
                scores[
                    RecoveryStrategy.RETRY_PAYMENT
                ],
                0.90,
            )

            scores[
                RecoveryStrategy.RECOVERY_LINK
            ] = max(
                scores[
                    RecoveryStrategy.RECOVERY_LINK
                ],
                0.35,
            )

        # -------------------------------------------------
        # Customer insufficient funds
        # -------------------------------------------------

        elif category == "customer_funds_issue":

            scores[
                RecoveryStrategy.SEND_REMINDER
            ] = max(
                scores[
                    RecoveryStrategy.SEND_REMINDER
                ],
                0.90,
            )

            scores[
                RecoveryStrategy.RECOVERY_LINK
            ] = max(
                scores[
                    RecoveryStrategy.RECOVERY_LINK
                ],
                0.70,
            )

            # Immediate retry is less useful when
            # insufficient funds are the cause.

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] *= 0.50

        # -------------------------------------------------
        # Authentication failure
        # -------------------------------------------------

        elif category == "authentication_failure":

            scores[
                RecoveryStrategy.RECOVERY_LINK
            ] = max(
                scores[
                    RecoveryStrategy.RECOVERY_LINK
                ],
                0.90,
            )

            scores[
                RecoveryStrategy.SEND_REMINDER
            ] = max(
                scores[
                    RecoveryStrategy.SEND_REMINDER
                ],
                0.40,
            )

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] *= 0.50

        # -------------------------------------------------
        # Payment declined
        # -------------------------------------------------

        elif category == "payment_declined":

            scores[
                RecoveryStrategy.RECOVERY_LINK
            ] = max(
                scores[
                    RecoveryStrategy.RECOVERY_LINK
                ],
                0.80,
            )

            scores[
                RecoveryStrategy.SEND_REMINDER
            ] = max(
                scores[
                    RecoveryStrategy.SEND_REMINDER
                ],
                0.50,
            )

            scores[
                RecoveryStrategy.RETRY_PAYMENT
            ] *= 0.60

        # -------------------------------------------------
        # Unknown failures
        # -------------------------------------------------

        elif category in {
            "unknown",
            "unknown_failure",
        }:

            scores[
                RecoveryStrategy.ESCALATE
            ] = max(
                scores[
                    RecoveryStrategy.ESCALATE
                ],
                0.70,
            )

            scores[
                RecoveryStrategy.NO_ACTION
            ] = max(
                scores[
                    RecoveryStrategy.NO_ACTION
                ],
                0.30,
            )

    # =====================================================
    # Decision Explanation
    # =====================================================

    def _build_reason(
        self,
        strategy: RecoveryStrategy,
        diagnosis: FailureDiagnosis,
        score: float,
    ) -> str:
        """
        Produce an explainable reason for every
        strategy score.
        """

        return (
            f"Strategy '{strategy.value}' received "
            f"a score of {round(score, 4)} based on "
            f"root cause category "
            f"'{diagnosis.category}'."
        )