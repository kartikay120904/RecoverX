from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentFailureCode,
    RecoveryStrategy,
)

from backend.app.domain.models import (
    Payment,
)

from simulator.analytics.incident_analysis import (
    IncidentAnalysis,
)

from simulator.analytics.recovery_recommendations import (
    RecoveryRecommendations,
)


def create_payment(
    *,
    amount: Decimal = Decimal("100.00"),
    failure_code: str | None = None,
) -> Payment:
    """
    Create a deterministic payment for
    recovery recommendation tests.
    """

    return Payment(
        payment_id=uuid4(),
        amount=amount,
        failure_code=failure_code,
    )


def create_incident(
    *,
    severity: str = "low",
) -> IncidentAnalysis:
    """
    Create a deterministic incident analysis
    for recovery recommendation tests.
    """

    return IncidentAnalysis(
        detected=(
            severity == "critical"
        ),
        severity=severity,
    )


# ============================================================
# RETRY PAYMENT STRATEGY
# ============================================================


def test_bank_timeout_recommends_retry_payment():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_network_error_recommends_retry_payment():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.NETWORK_ERROR.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


def test_gateway_timeout_recommends_retry_payment():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.GATEWAY_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.RETRY_PAYMENT
    )


# ============================================================
# SEND REMINDER STRATEGY
# ============================================================


def test_authentication_failure_recommends_reminder():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode
            .AUTHENTICATION_FAILED
            .value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.SEND_REMINDER
    )


def test_insufficient_funds_recommends_reminder():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode
            .INSUFFICIENT_FUNDS
            .value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.SEND_REMINDER
    )


# ============================================================
# RECOVERY LINK STRATEGY
# ============================================================


def test_payment_declined_recommends_recovery_link():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode
            .PAYMENT_DECLINED
            .value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.RECOVERY_LINK
    )


# ============================================================
# UNKNOWN FAILURE
# ============================================================


def test_unknown_failure_recommends_no_action():

    payment = create_payment(
        failure_code="unknown_failure",
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.NO_ACTION
    )


# ============================================================
# CRITICAL INCIDENT
# ============================================================


def test_critical_incident_recommends_escalation():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(
                severity="critical",
            ),
        )
    )

    assert (
        recommendation.strategy
        == RecoveryStrategy.ESCALATE
    )


# ============================================================
# PROBABILITY
# ============================================================


def test_retry_payment_probability():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.predicted_probability
        == 0.65
    )


def test_reminder_probability():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode
            .INSUFFICIENT_FUNDS
            .value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.predicted_probability
        == 0.35
    )


def test_recovery_link_probability():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode
            .PAYMENT_DECLINED
            .value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.predicted_probability
        == 0.45
    )


def test_escalation_probability():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(
                severity="critical",
            ),
        )
    )

    assert (
        recommendation.predicted_probability
        == 0.10
    )


# ============================================================
# PREDICTED REVENUE
# ============================================================


def test_predicted_revenue_is_calculated_correctly():

    payment = create_payment(
        amount=Decimal("1000.00"),
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.predicted_revenue
        == Decimal("650.000")
    )


def test_no_action_has_zero_predicted_revenue():

    payment = create_payment(
        amount=Decimal("1000.00"),
        failure_code="unknown_failure",
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert (
        recommendation.predicted_revenue
        == Decimal("0.000")
    )


# ============================================================
# BATCH RECOMMENDATIONS
# ============================================================


def test_recommend_many_only_includes_failed_payments():

    successful_payment = create_payment(
        failure_code=None,
    )

    failed_payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendations = (
        RecoveryRecommendations().recommend_many(
            payments=[
                successful_payment,
                failed_payment,
            ],
            incident=create_incident(),
        )
    )

    assert len(recommendations) == 1

    assert (
        recommendations[0].payment_id
        == str(
            failed_payment.payment_id
        )
    )


def test_recommend_many_returns_empty_for_no_failed_payments():

    payment = create_payment(
        failure_code=None,
    )

    recommendations = (
        RecoveryRecommendations().recommend_many(
            payments=[payment],
            incident=create_incident(),
        )
    )

    assert recommendations == []


def test_recommend_many_returns_empty_for_empty_payment_list():

    recommendations = (
        RecoveryRecommendations().recommend_many(
            payments=[],
            incident=create_incident(),
        )
    )

    assert recommendations == []


# ============================================================
# IMMUTABILITY
# ============================================================


def test_recommendation_does_not_modify_payment():

    payment = create_payment(
        amount=Decimal("500.00"),
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    original_amount = payment.amount

    original_failure_code = (
        payment.failure_code
    )

    RecoveryRecommendations().recommend(
        payment=payment,
        incident=create_incident(),
    )

    assert (
        payment.amount
        == original_amount
    )

    assert (
        payment.failure_code
        == original_failure_code
    )


# ============================================================
# REASON
# ============================================================


def test_recommendation_contains_reason():

    payment = create_payment(
        failure_code=(
            PaymentFailureCode.BANK_TIMEOUT.value
        ),
    )

    recommendation = (
        RecoveryRecommendations().recommend(
            payment=payment,
            incident=create_incident(),
        )
    )

    assert recommendation.reason

    assert (
        "BANK_TIMEOUT"
        in recommendation.reason
        or payment.failure_code
        in recommendation.reason
    )