from dataclasses import dataclass


@dataclass(frozen=True)
class EscalationDecision:
    should_escalate: bool
    reason: str | None = None


class EscalationPolicy:
    """
    Determines whether a recovery attempt should be
    escalated for human review.
    """

    def evaluate(
        self,
        *,
        retry_limit_reached: bool = False,
        requires_human_approval: bool = False,
        confidence: float | None = None,
        minimum_confidence: float = 0.5,
        payment_amount: float | None = None,
        high_value_threshold: float | None = None,
        execution_failures: int = 0,
        max_execution_failures: int = 2,
        has_recovery_action: bool = True,
    ) -> EscalationDecision:

        if retry_limit_reached:
            return EscalationDecision(
                should_escalate=True,
                reason="retry limit exceeded",
            )

        if requires_human_approval:
            return EscalationDecision(
                should_escalate=True,
                reason="recovery requires human approval",
            )

        if (
            confidence is not None
            and confidence < minimum_confidence
        ):
            return EscalationDecision(
                should_escalate=True,
                reason="recovery confidence too low",
            )

        if (
            payment_amount is not None
            and high_value_threshold is not None
            and payment_amount >= high_value_threshold
        ):
            return EscalationDecision(
                should_escalate=True,
                reason="high-value payment requires review",
            )

        if execution_failures >= max_execution_failures:
            return EscalationDecision(
                should_escalate=True,
                reason="recovery execution repeatedly failed",
            )

        if not has_recovery_action:
            return EscalationDecision(
                should_escalate=True,
                reason="no recovery action available",
            )

        return EscalationDecision(
            should_escalate=False,
            reason=None,
        )