from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment


@dataclass(frozen=True)
class StrategyDecision:
    """
    Represents a scored recovery decision for a
    failed payment.

    The decision engine is deterministic and does
    not modify the original payment.
    """

    strategy: RecoveryStrategy

    predicted_probability: float

    predicted_revenue: Decimal

    decision_score: float

    reason: str


def _normalize_failure_code(
    failure_code,
) -> str | None:
    """
    Normalize enum and string failure codes.
    """

    if failure_code is None:
        return None

    if hasattr(failure_code, "value"):
        return str(failure_code.value)

    return str(failure_code)


def _clamp_probability(
    probability: float,
) -> float:
    """
    Ensure probability remains between 0 and 1.
    """

    return max(
        0.0,
        min(
            1.0,
            probability,
        ),
    )


def _calculate_predicted_revenue(
    amount: Decimal,
    probability: float,
) -> Decimal:
    """
    Calculate expected recoverable revenue.
    """

    return (
        amount
        * Decimal(
            str(probability)
        )
    ).quantize(
        Decimal("0.01")
    )


def _strategy_probability(
    failure_code: str | None,
    strategy: RecoveryStrategy,
) -> tuple[float, str]:
    """
    Return a deterministic recovery probability
    and explanation for a strategy.

    These are baseline heuristic probabilities.
    They can later be replaced by an ML model
    without changing the public API.
    """

    timeout_codes = {
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
    }

    # ---------------------------------------------
    # Infrastructure / transient failures
    # ---------------------------------------------

    if failure_code in timeout_codes:

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):
            return (
                0.85,
                "The failure appears transient, so "
                "a controlled retry has a high "
                "probability of recovery.",
            )

        if (
            strategy
            == RecoveryStrategy.ESCALATE
        ):
            return (
                0.35,
                "Escalation is possible, but a "
                "controlled retry is more suitable "
                "for a transient infrastructure "
                "failure.",
            )

        return (
            0.20,
            "This strategy is less suitable for "
            "a transient payment infrastructure "
            "failure.",
        )

    # ---------------------------------------------
    # Insufficient funds
    # ---------------------------------------------

    if (
        failure_code
        == PaymentFailureCode.INSUFFICIENT_FUNDS.value
    ):

        if (
            strategy
            == RecoveryStrategy.SEND_REMINDER
        ):
            return (
                0.65,
                "Waiting and sending a reminder "
                "gives the customer time to restore "
                "available funds.",
            )

        if (
            strategy
            == RecoveryStrategy.RECOVERY_LINK
        ):
            return (
                0.45,
                "A recovery link can help the "
                "customer retry using another "
                "payment method.",
            )

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):
            return (
                0.25,
                "An immediate retry is less likely "
                "to succeed while funds remain "
                "insufficient.",
            )

        return (
            0.30,
            "Escalation is possible but is not "
            "the preferred first recovery action.",
        )

    # ---------------------------------------------
    # Authentication failures
    # ---------------------------------------------

    if (
        failure_code
        == PaymentFailureCode.AUTHENTICATION_FAILED.value
    ):

        if (
            strategy
            == RecoveryStrategy.RECOVERY_LINK
        ):
            return (
                0.80,
                "The customer can complete the "
                "required authentication through "
                "a recovery flow.",
            )

        if (
            strategy
            == RecoveryStrategy.ESCALATE
        ):
            return (
                0.70,
                "Customer intervention can resolve "
                "authentication issues.",
            )

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):
            return (
                0.20,
                "Retrying without new authentication "
                "is unlikely to resolve the failure.",
            )

        return (
            0.35,
            "A reminder alone may not resolve an "
            "authentication requirement.",
        )

    # ---------------------------------------------
    # Payment declined
    # ---------------------------------------------

    if (
        failure_code
        == PaymentFailureCode.PAYMENT_DECLINED.value
    ):

        if (
            strategy
            == RecoveryStrategy.RECOVERY_LINK
        ):
            return (
                0.70,
                "A recovery link allows the customer "
                "to retry with another payment method.",
            )

        if (
            strategy
            == RecoveryStrategy.SEND_REMINDER
        ):
            return (
                0.50,
                "A reminder can encourage the customer "
                "to retry later.",
            )

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):
            return (
                0.30,
                "Repeating the same declined payment "
                "may not resolve the underlying issue.",
            )

        return (
            0.45,
            "Escalation can help when automated "
            "recovery is unsuccessful.",
        )

    # ---------------------------------------------
    # Unknown failure
    # ---------------------------------------------

    if (
        strategy
        == RecoveryStrategy.RETRY_PAYMENT
    ):
        return (
            0.45,
            "The failure reason is unknown, so a "
            "single controlled retry is a reasonable "
            "initial recovery action.",
        )

    if (
        strategy
        == RecoveryStrategy.RECOVERY_LINK
    ):
        return (
            0.50,
            "A recovery link allows the customer "
            "to retry using a different flow.",
        )

    if (
        strategy
        == RecoveryStrategy.SEND_REMINDER
    ):
        return (
            0.40,
            "A reminder may encourage a later "
            "payment attempt.",
        )

    return (
        0.35,
        "Escalation is available when automated "
        "recovery confidence is limited.",
    )


def generate_strategy_candidates(
    payment: Payment,
) -> list[RecoveryStrategy]:
    """
    Generate valid candidate strategies.

    NO_ACTION is intentionally excluded because
    this engine is used for failed payments that
    require recovery evaluation.
    """

    return [
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStrategy.SEND_REMINDER,
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStrategy.ESCALATE,
    ]


def score_strategy(
    payment: Payment,
    strategy: RecoveryStrategy,
    incident_severity: str = "normal",
) -> StrategyDecision:
    """
    Score one recovery strategy for a payment.

    decision_score is currently based primarily on
    recovery probability with a small severity-aware
    priority adjustment.

    The API is intentionally simple so future ML
    predictions can replace the heuristic layer.
    """

    failure_code = _normalize_failure_code(
        payment.failure_code
    )

    probability, reason = (
        _strategy_probability(
            failure_code,
            strategy,
        )
    )

    probability = _clamp_probability(
        probability
    )

    predicted_revenue = (
        _calculate_predicted_revenue(
            payment.amount,
            probability,
        )
    )

    severity_weights = {
        "normal": 0.00,
        "none": 0.00,
        "medium": 0.03,
        "high": 0.06,
        "critical": 0.10,
    }

    severity_bonus = (
        severity_weights.get(
            incident_severity.lower(),
            0.00,
        )
    )

    decision_score = (
        probability
        + severity_bonus
    )

    decision_score = min(
        1.0,
        round(
            decision_score,
            4,
        ),
    )

    return StrategyDecision(
        strategy=strategy,
        predicted_probability=probability,
        predicted_revenue=predicted_revenue,
        decision_score=decision_score,
        reason=reason,
    )


def rank_strategies(
    payment: Payment,
    incident_severity: str = "normal",
) -> list[StrategyDecision]:
    """
    Score and rank all recovery strategies.

    Highest decision score appears first.
    Ties are resolved deterministically using
    strategy value.
    """

    decisions = [
        score_strategy(
            payment,
            strategy,
            incident_severity,
        )
        for strategy in (
            generate_strategy_candidates(
                payment
            )
        )
    ]

    return sorted(
        decisions,
        key=lambda decision: (
            -decision.decision_score,
            -decision.predicted_probability,
            str(decision.strategy.value),
        ),
    )


def select_best_strategy(
    payment: Payment,
    incident_severity: str = "normal",
) -> StrategyDecision:
    """
    Select the highest scoring recovery strategy.
    """

    decisions = rank_strategies(
        payment,
        incident_severity,
    )

    return decisions[0]


def build_recovery_attempt_data(
    payment: Payment,
    incident_severity: str = "normal",
) -> dict:
    """
    Build data compatible with the existing
    RecoveryAttempt model.

    This function does NOT create or persist
    anything. It only returns compatible data.
    """

    decision = select_best_strategy(
        payment,
        incident_severity,
    )

    return {
        "payment_id": payment.payment_id,
        "strategy": decision.strategy,
        "predicted_probability": (
            decision.predicted_probability
        ),
        "predicted_revenue": (
            decision.predicted_revenue
        ),
        "decision_score": (
            decision.decision_score
        ),
        "reason": decision.reason,
    }