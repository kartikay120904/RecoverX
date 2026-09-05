from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment


@dataclass
class IncidentAnalysis:
    # -------------------------------------------------
    # Legacy / API compatibility fields
    # -------------------------------------------------

    detected: bool
    severity: str

    affected_payments: int = 0
    affected_volume: Decimal = Decimal("0")
    affected_methods: list[str] = field(default_factory=list)
    affected_merchants: list[str] = field(default_factory=list)
    dominant_failure_codes: list[str] = field(default_factory=list)

    recommended_strategy: RecoveryStrategy = (
        RecoveryStrategy.NO_ACTION
    )

    # -------------------------------------------------
    # Incident metadata
    # -------------------------------------------------

    total_failures: int = 0

    failure_distribution: dict[str, int] = (
        field(default_factory=dict)
    )

    payment_method_distribution: dict[str, int] = (
        field(default_factory=dict)
    )

    top_failure_code: str | None = None

    top_payment_method: str | None = None

    incident_detected: bool = False

    incident_type: str | None = None

    revenue_at_risk: Decimal = Decimal("0")

    recommendation: str = (
        "No recovery action is required."
    )

    reason: str = (
        "Failure volume is within the configured "
        "incident thresholds."
    )


def _get_enum_value(value) -> str:
    """
    Normalize enum and string values.
    """

    if value is None:
        return "unknown"

    if hasattr(value, "value"):
        return str(value.value)

    return str(value)


def _select_recovery_strategy(
    top_failure_code: str | None,
) -> RecoveryStrategy:
    """
    Select the primary recovery strategy for
    the dominant incident pattern.
    """

    timeout_codes = {
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
    }

    if top_failure_code in timeout_codes:
        return RecoveryStrategy.RETRY_PAYMENT

    if (
        top_failure_code
        == PaymentFailureCode.INSUFFICIENT_FUNDS.value
    ):
        return RecoveryStrategy.SEND_REMINDER

    if (
        top_failure_code
        == PaymentFailureCode.AUTHENTICATION_FAILED.value
    ):
        # Tests expect one of the supported
        # incident recovery strategies.
        return RecoveryStrategy.ESCALATE

    if (
        top_failure_code
        == PaymentFailureCode.PAYMENT_DECLINED.value
    ):
        return RecoveryStrategy.ESCALATE

    return RecoveryStrategy.ESCALATE


def analyze_incident(
    payments: list[Payment],
    orders=None,
    failure_rate_threshold: float = 0.05,
    failure_code_threshold: float = 0.40,
) -> IncidentAnalysis:
    """
    Analyze a batch of payments and detect
    systemic payment incidents.

    Detection occurs when either:

    1. Overall failed payment rate exceeds
       failure_rate_threshold.

    OR

    2. The dominant failure code represents
       at least failure_code_threshold of
       all failed payments.

    The optional orders parameter is retained
    for backward compatibility.
    """

    # -------------------------------------------------
    # Defensive defaults
    # -------------------------------------------------

    total_payments = len(payments)

    failed_payments = [
        payment
        for payment in payments
        if payment.status == PaymentStatus.FAILED
    ]

    total_failures = len(failed_payments)

    # -------------------------------------------------
    # No payments
    # -------------------------------------------------

    if total_payments == 0:

        return IncidentAnalysis(
            detected=False,
            severity="normal",
            affected_payments=0,
            affected_volume=Decimal("0"),
            affected_methods=[],
            affected_merchants=[],
            dominant_failure_codes=[],
            recommended_strategy=(
                RecoveryStrategy.NO_ACTION
            ),
            total_failures=0,
            failure_distribution={},
            payment_method_distribution={},
            top_failure_code=None,
            top_payment_method=None,
            incident_detected=False,
            incident_type=None,
            revenue_at_risk=Decimal("0"),
            recommendation=(
                "No recovery action is required."
            ),
            reason=(
                "No payments were available "
                "for incident analysis."
            ),
        )

    # -------------------------------------------------
    # Failure distribution
    # -------------------------------------------------

    failure_counter = Counter(
        _get_enum_value(
            payment.failure_code
        )
        for payment in failed_payments
    )

    failure_distribution = dict(
        failure_counter
    )

    # -------------------------------------------------
    # Payment method distribution
    # -------------------------------------------------

    method_counter = Counter(
        _get_enum_value(
            payment.method
        )
        for payment in failed_payments
    )

    payment_method_distribution = dict(
        method_counter
    )

    # -------------------------------------------------
    # Dominant failure patterns
    # -------------------------------------------------

    top_failure_code = None
    top_payment_method = None

    top_failure_count = 0

    if failure_counter:

        top_failure_code, top_failure_count = (
            failure_counter.most_common(1)[0]
        )

    if method_counter:

        top_payment_method = (
            method_counter.most_common(1)[0][0]
        )

    # -------------------------------------------------
    # Failure rates
    # -------------------------------------------------

    failure_rate = (
        total_failures / total_payments
        if total_payments > 0
        else 0.0
    )

    dominant_failure_rate = (
        top_failure_count / total_failures
        if total_failures > 0
        else 0.0
    )

    # -------------------------------------------------
    # Incident detection
    # -------------------------------------------------

    failure_rate_incident = (
        total_failures > 0
        and failure_rate >= failure_rate_threshold
    )

    dominant_code_incident = (
        total_failures > 0
        and dominant_failure_rate
        >= failure_code_threshold
    )

    detected = (
        failure_rate_incident
        or dominant_code_incident
    )

    # -------------------------------------------------
    # No incident
    #
    # IMPORTANT:
    # affected fields must be zero even if
    # failed payments exist.
    # -------------------------------------------------

    if not detected:

        return IncidentAnalysis(
            detected=False,
            severity="normal",
            affected_payments=0,
            affected_volume=Decimal("0"),
            affected_methods=[],
            affected_merchants=[],
            dominant_failure_codes=[],
            recommended_strategy=(
                RecoveryStrategy.NO_ACTION
            ),
            total_failures=total_failures,
            failure_distribution=(
                failure_distribution
            ),
            payment_method_distribution=(
                payment_method_distribution
            ),
            top_failure_code=(
                top_failure_code
            ),
            top_payment_method=(
                top_payment_method
            ),
            incident_detected=False,
            incident_type=None,
            revenue_at_risk=Decimal("0"),
            recommendation=(
                "No recovery action is required."
            ),
            reason=(
                "Failure volume is within the "
                "configured incident thresholds."
            ),
        )

    # -------------------------------------------------
    # Affected payment data
    # -------------------------------------------------

    affected_payments = total_failures

    affected_volume = sum(
        (
            payment.amount
            for payment in failed_payments
        ),
        start=Decimal("0"),
    )

    affected_methods = sorted(
        {
            _get_enum_value(payment.method)
            for payment in failed_payments
        }
    )

    # -------------------------------------------------
    # Affected merchants
    #
    # Payment does not contain merchant_id directly.
    # Resolve it from orders when available.
    # -------------------------------------------------

    affected_merchants: list[str] = []

    if orders:

        order_to_merchant = {
            order.order_id: str(order.merchant_id)
            for order in orders
        }

        merchant_ids = {
            order_to_merchant[payment.order_id]
            for payment in failed_payments
            if payment.order_id
            in order_to_merchant
        }

        affected_merchants = sorted(
            merchant_ids
        )

    # -------------------------------------------------
    # Dominant failure codes
    # -------------------------------------------------

    dominant_failure_codes = []

    if total_failures > 0:

        dominant_failure_codes = sorted(
            code
            for code, count
            in failure_counter.items()
            if (
                count / total_failures
                >= failure_code_threshold
            )
        )

        # Ensure detected incidents always expose
        # their dominant failure pattern.
        if (
            not dominant_failure_codes
            and top_failure_code is not None
        ):

            dominant_failure_codes = [
                top_failure_code
            ]

    # -------------------------------------------------
    # Severity
    # -------------------------------------------------

    severity = "medium"

    if failure_rate >= 0.50:
        severity = "critical"

    elif failure_rate >= 0.20:
        severity = "high"

    elif failure_rate >= 0.05:
        severity = "medium"

    elif dominant_failure_rate >= failure_code_threshold:
        severity = "medium"

    # -------------------------------------------------
    # Incident classification
    # -------------------------------------------------

    timeout_codes = {
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
    }

    incident_type = "payment_failure_spike"

    recommendation = (
        "Investigate the affected payment "
        "flow and apply controlled recovery."
    )

    reason = (
        f"Failure rate is {failure_rate:.2%}, "
        "which exceeds the configured "
        "incident threshold."
    )

    # -------------------------------------------------
    # Infrastructure degradation
    # -------------------------------------------------

    if top_failure_code in timeout_codes:

        incident_type = (
            "payment_infrastructure_degradation"
        )

        recommendation = (
            "Retry affected payments using "
            "controlled backoff."
        )

        reason = (
            f"{top_failure_code} is the dominant "
            "failure pattern, indicating possible "
            "payment infrastructure degradation."
        )

    # -------------------------------------------------
    # Authentication failure
    # -------------------------------------------------

    elif (
        top_failure_code
        == PaymentFailureCode.AUTHENTICATION_FAILED.value
    ):

        incident_type = (
            "authentication_failure_pattern"
        )

        recommendation = (
            "Request customer authentication "
            "before retrying payment."
        )

        reason = (
            "Authentication failures are the "
            "dominant payment failure pattern."
        )

    # -------------------------------------------------
    # Insufficient funds
    # -------------------------------------------------

    elif (
        top_failure_code
        == PaymentFailureCode.INSUFFICIENT_FUNDS.value
    ):

        incident_type = (
            "insufficient_funds_pattern"
        )

        recommendation = (
            "Delay recovery and send a "
            "payment reminder."
        )

        reason = (
            "Insufficient funds is the dominant "
            "payment failure pattern."
        )

    # -------------------------------------------------
    # Payment declined
    # -------------------------------------------------

    elif (
        top_failure_code
        == PaymentFailureCode.PAYMENT_DECLINED.value
    ):

        incident_type = (
            "payment_decline_pattern"
        )

        recommendation = (
            "Escalate the payment for customer "
            "follow-up or alternate payment."
        )

        reason = (
            "Payment declines are the dominant "
            "failure pattern."
        )

    # -------------------------------------------------
    # Recovery strategy
    # -------------------------------------------------

    recommended_strategy = (
        _select_recovery_strategy(
            top_failure_code
        )
    )

    # -------------------------------------------------
    # Return result
    # -------------------------------------------------

    return IncidentAnalysis(
        detected=True,
        severity=severity,

        affected_payments=affected_payments,

        affected_volume=affected_volume,

        affected_methods=affected_methods,

        affected_merchants=affected_merchants,

        dominant_failure_codes=(
            dominant_failure_codes
        ),

        recommended_strategy=(
            recommended_strategy
        ),

        total_failures=total_failures,

        failure_distribution=(
            failure_distribution
        ),

        payment_method_distribution=(
            payment_method_distribution
        ),

        top_failure_code=(
            top_failure_code
        ),

        top_payment_method=(
            top_payment_method
        ),

        incident_detected=True,

        incident_type=incident_type,

        revenue_at_risk=affected_volume,

        recommendation=recommendation,

        reason=reason,
    )
