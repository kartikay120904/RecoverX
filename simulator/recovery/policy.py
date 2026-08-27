from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import Payment, RecoveryAttempt


@dataclass(frozen=True)
class RecoveryPolicy:
    """
    Safety policy controlling whether RecoverX may execute
    a proposed recovery action automatically.
    """

    max_retries: int = 2
    max_auto_recovery_amount: Decimal = Decimal("50000")
    minimum_confidence: float = 0.70
    require_approval_above_amount: Decimal = Decimal("10000")


@dataclass(frozen=True)
class PolicyDecision:
    """
    Result of evaluating a recovery attempt against policy.
    """

    allowed: bool
    requires_approval: bool
    reason: str
    risk_level: str


class RecoveryPolicyEngine:
    """
    Evaluates recovery attempts before execution.

    The policy engine is intentionally deterministic.
    AI may recommend an action, but policy decides whether
    that action is safe to execute.
    """

    def __init__(
        self,
        policy: RecoveryPolicy | None = None,
    ) -> None:
        self.policy = policy or RecoveryPolicy()

    def evaluate(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
    ) -> PolicyDecision:

        # ---------------------------------------------
        # Strategy safety
        # ---------------------------------------------

        if attempt.strategy == RecoveryStrategy.NO_ACTION:
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason="No recovery action was recommended.",
                risk_level="low",
            )

        # ---------------------------------------------
        # Retry limit
        # ---------------------------------------------

        if (
            attempt.strategy == RecoveryStrategy.RETRY_PAYMENT
            and payment.attempt_number >= self.policy.max_retries
        ):
            return PolicyDecision(
                allowed=False,
                requires_approval=False,
                reason=(
                    f"Retry limit reached: "
                    f"{payment.attempt_number} attempts."
                ),
                risk_level="high",
            )

        # ---------------------------------------------
        # Confidence guardrail
        # ---------------------------------------------

        if (
            attempt.predicted_probability
            < self.policy.minimum_confidence
        ):
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                reason=(
                    "Predicted recovery probability is below "
                    f"the automatic execution threshold of "
                    f"{self.policy.minimum_confidence:.0%}."
                ),
                risk_level="medium",
            )

        # ---------------------------------------------
        # High-value transaction protection
        # ---------------------------------------------

        if (
            payment.amount
            > self.policy.max_auto_recovery_amount
        ):
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                reason=(
                    "Payment exceeds the maximum amount allowed "
                    "for automatic recovery."
                ),
                risk_level="high",
            )

        # ---------------------------------------------
        # Additional approval threshold
        # ---------------------------------------------

        if (
            payment.amount
            > self.policy.require_approval_above_amount
        ):
            return PolicyDecision(
                allowed=True,
                requires_approval=True,
                reason=(
                    "High-value recovery requires human approval."
                ),
                risk_level="medium",
            )

        # ---------------------------------------------
        # Safe automatic execution
        # ---------------------------------------------

        return PolicyDecision(
            allowed=True,
            requires_approval=False,
            reason="Recovery action passed all safety checks.",
            risk_level="low",
        )