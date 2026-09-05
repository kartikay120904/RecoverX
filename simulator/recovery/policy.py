from dataclasses import dataclass

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)


@dataclass(frozen=True)
class RecoveryPolicyDecision:
    """
    Final policy decision for a recovery attempt.
    """

    allowed: bool

    requires_approval: bool

    risk_level: str

    reason: str


class RecoveryPolicyEngine:
    """
    Applies business-level policy rules to recovery attempts.

    This layer decides whether a proposed recovery may proceed
    automatically, requires human approval, or must be blocked.
    """

    MAX_RETRY_ATTEMPTS = 2

    LOW_CONFIDENCE_THRESHOLD = 0.70

    HIGH_VALUE_THRESHOLD = 50_000

    TERMINAL_STATUSES = {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
        RecoveryStatus.REJECTED,
    }

    def evaluate(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
    ) -> RecoveryPolicyDecision:

        # ---------------------------------------------
        # Rule 1: Terminal recovery attempts
        # ---------------------------------------------

        if attempt.status in self.TERMINAL_STATUSES:

            return RecoveryPolicyDecision(
                allowed=False,
                requires_approval=False,
                risk_level="high",
                reason=(
                    "Recovery attempt is already in a "
                    "terminal state."
                ),
            )

        # ---------------------------------------------
        # Rule 2: Explicit no-action strategy
        # ---------------------------------------------

        if (
            attempt.strategy
            == RecoveryStrategy.NO_ACTION
        ):

            return RecoveryPolicyDecision(
                allowed=False,
                requires_approval=False,
                risk_level="low",
                reason=(
                    "No recovery action was selected."
                ),
            )

        # ---------------------------------------------
        # Rule 3: Retry limit
        #
        # attempt_number=2 is blocked according
        # to the existing test contract.
        # ---------------------------------------------

        if (
            payment.attempt_number
            >= self.MAX_RETRY_ATTEMPTS
        ):

            return RecoveryPolicyDecision(
                allowed=False,
                requires_approval=False,
                risk_level="high",
                reason=(
                    "Retry limit reached. "
                    "Automatic recovery is blocked."
                ),
            )

        # ---------------------------------------------
        # Rule 4: Escalation strategy
        # ---------------------------------------------

        if (
            attempt.strategy
            == RecoveryStrategy.ESCALATE
        ):

            return RecoveryPolicyDecision(
                allowed=True,
                requires_approval=True,
                risk_level="high",
                reason=(
                    "Recovery requires human escalation."
                ),
            )

        # ---------------------------------------------
        # Rule 5: High-value payment
        # ---------------------------------------------

        if (
            payment.amount
            >= self.HIGH_VALUE_THRESHOLD
        ):

            return RecoveryPolicyDecision(
                allowed=True,
                requires_approval=True,
                risk_level="high",
                reason=(
                    "High-value recovery requires "
                    "human approval."
                ),
            )

        # ---------------------------------------------
        # Rule 6: Low-confidence decision
        # ---------------------------------------------

        if (
            attempt.predicted_probability
            < self.LOW_CONFIDENCE_THRESHOLD
        ):

            return RecoveryPolicyDecision(
                allowed=True,
                requires_approval=True,
                risk_level="medium",
                reason=(
                    "Recovery confidence is below the "
                    "automatic execution threshold."
                ),
            )

        # ---------------------------------------------
        # Safe automatic recovery
        # ---------------------------------------------

        return RecoveryPolicyDecision(
            allowed=True,
            requires_approval=False,
            risk_level="low",
            reason=(
                "Recovery satisfies automatic "
                "execution policy."
            ),
        )