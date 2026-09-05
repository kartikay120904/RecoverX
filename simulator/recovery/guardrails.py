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
class RecoveryGuardrailDecision:
    """
    Result of evaluating whether a recovery attempt
    is allowed to continue.
    """

    allowed: bool

    action: str

    reason: str

    should_escalate: bool = False

    cooldown_required: bool = False

    should_stop: bool = False


class RecoveryGuardrails:
    """
    Enforces bounded recovery behavior.

    Guardrails prevent:

    - unlimited retries
    - unsafe repeated recovery attempts
    - execution of terminal recovery attempts
    - execution when NO_ACTION is selected
    - uncontrolled automatic escalation
    """

    MAX_RETRY_ATTEMPTS = 3

    TERMINAL_STATUSES = {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
        RecoveryStatus.REJECTED,
    }

    def evaluate(
        self,
        payment: Payment,
        attempt: RecoveryAttempt,
    ) -> RecoveryGuardrailDecision:

        # ---------------------------------------------
        # Guardrail 1: Terminal recovery states
        # ---------------------------------------------

        if (
            attempt.status
            in self.TERMINAL_STATUSES
        ):

            return RecoveryGuardrailDecision(
                allowed=False,
                action="stop",
                reason=(
                    "Recovery attempt is already in "
                    "a terminal state."
                ),
                should_stop=True,
            )

        # ---------------------------------------------
        # Guardrail 2: Maximum retry attempts
        # ---------------------------------------------

        if (
            payment.attempt_number
            >= self.MAX_RETRY_ATTEMPTS
        ):

            return RecoveryGuardrailDecision(
                allowed=False,
                action="stop",
                reason=(
                    "Maximum recovery retry limit "
                    "reached."
                ),
                should_escalate=True,
                should_stop=True,
            )

        # ---------------------------------------------
        # Guardrail 3: No-action strategy
        # ---------------------------------------------

        if (
            attempt.strategy
            == RecoveryStrategy.NO_ACTION
        ):

            return RecoveryGuardrailDecision(
                allowed=False,
                action="stop",
                reason=(
                    "Recovery engine selected "
                    "NO_ACTION."
                ),
                should_stop=True,
            )

        # ---------------------------------------------
        # Guardrail 4: Escalation
        # ---------------------------------------------

        if (
            attempt.strategy
            == RecoveryStrategy.ESCALATE
        ):

            return RecoveryGuardrailDecision(
                allowed=False,
                action="escalate",
                reason=(
                    "Recovery requires human "
                    "escalation."
                ),
                should_escalate=True,
            )

        # ---------------------------------------------
        # Guardrail 5: Retry cooldown
        #
        # Repeated automatic retry should not happen
        # immediately.
        # ---------------------------------------------

        if (
            payment.attempt_number > 1
            and attempt.strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):

            return RecoveryGuardrailDecision(
                allowed=False,
                action="cooldown",
                reason=(
                    "Repeated retry requires a "
                    "cooldown period."
                ),
                cooldown_required=True,
            )

        # ---------------------------------------------
        # Recovery allowed
        # ---------------------------------------------

        return RecoveryGuardrailDecision(
            allowed=True,
            action="execute",
            reason=(
                "Recovery attempt passed all "
                "guardrail checks."
            ),
        )