from decimal import Decimal
from random import Random
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    Payment,
    RecoveryEvent,
)

from simulator.analytics.counterfactual import (
    simulate_counterfactuals,
)
from simulator.analytics.incident_analysis import (
    IncidentAnalysis,
)
from simulator.recovery.engine import RecoveryEngine
from simulator.recovery.executor import RecoveryExecutor
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig
from backend.app.domain.state_machine import (
    InvalidRecoveryTransition,
    transition_recovery,
)

router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"],
)


# =========================================================
# Runtime stores
# =========================================================

payments_store: dict[UUID, Payment] = {}

recovery_store: dict[UUID, Any] = {}

orders_store: dict[UUID, Any] = {}

customers_store: dict[UUID, Any] = {}

merchants_store: dict[UUID, Any] = {}

# =========================================================
# Idempotency store
# =========================================================

idempotency_store: dict[str, dict] = {}

# =========================================================
# Recovery event store
# =========================================================

event_store: dict[UUID, list[RecoveryEvent]] = {}

# =========================================================
# Recovery services
# =========================================================

engine = RecoveryEngine()

executor = RecoveryExecutor()

random_generator = Random(42)

# =========================================================
# Recovery Event Recording Helper
# =========================================================

def _get_recovery_event_fields() -> dict[str, Any]:
    """
    Return the field map for the active RecoveryEvent model.
    """

    model_fields = getattr(
        RecoveryEvent,
        "model_fields",
        None,
    )

    if model_fields is not None:
        return model_fields

    return {}


def _is_required_event_field(
    field_name: str,
) -> bool:
    """
    Detect required fields across Pydantic versions.
    """

    field = _get_recovery_event_fields().get(
        field_name
    )

    if field is None:
        return False

    is_required = getattr(
        field,
        "is_required",
        None,
    )

    if callable(
        is_required
    ):
        return bool(
            is_required()
        )

    return bool(
        getattr(
            field,
            "required",
            False,
        )
    )


def _normalize_event_value(
    value: Any,
) -> str | int | float | bool | None:
    """
    Convert event metadata values into a Pydantic-safe scalar.
    """

    if value is None:
        return None

    if hasattr(
        value,
        "value",
    ):
        value = value.value

    if isinstance(
        value,
        Decimal,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        UUID,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return str(
        value
    )


def _normalize_event_metadata(
    metadata: dict[str, Any],
) -> dict[str, str | int | float | bool | None]:
    """
    Normalize metadata so it works with both `data`
    and `metadata` RecoveryEvent payload fields.
    """

    return {
        str(key): _normalize_event_value(
            value
        )
        for key, value
        in metadata.items()
    }


def _normalize_event_status(
    status: RecoveryStatus | str | None,
) -> str | None:
    """
    Normalize RecoveryStatus values without forcing optional
    event models to receive a fake status.
    """

    if status is None:
        return None

    if hasattr(
        status,
        "value",
    ):
        return status.value

    return str(
        status
    )


def _record_recovery_event(
    *,
    payment_id: UUID,
    event_type: str,
    status: RecoveryStatus | str | None = None,
    data: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    actor: str | None = None,
    strategy: RecoveryStrategy | str | None = None,
    details: str | None = None,
    **kwargs,
) -> RecoveryEvent:
    """
    Record a recovery lifecycle event for a payment.

    Events are stored in memory and can later be retrieved
    using GET /recovery/{payment_id}/events.
    """

    event_metadata: dict[str, Any] = {
        **(data or {}),
        **(metadata or {}),
    }

    if actor is not None:
        event_metadata[
            "actor"
        ] = actor

    for key, value in kwargs.items():

        if value is None:
            continue

        event_metadata[
            key
        ] = value

    event_metadata = _normalize_event_metadata(
        event_metadata
    )

    event_status = _normalize_event_status(
        status
    )

    if (
        event_status is None
        and _is_required_event_field(
            "status"
        )
    ):
        event_status = "unknown"

    event_fields = _get_recovery_event_fields()

    event_payload: dict[str, Any] = {
        "payment_id": payment_id,
        "event_type": event_type,
    }

    if "status" in event_fields:
        event_payload[
            "status"
        ] = event_status

    if "data" in event_fields:
        event_payload[
            "data"
        ] = event_metadata

    if "metadata" in event_fields:
        event_payload[
            "metadata"
        ] = event_metadata

    if (
        "actor" in event_fields
        and actor is not None
    ):
        event_payload[
            "actor"
        ] = actor

    if (
        "strategy" in event_fields
        and strategy is not None
    ):
        event_payload[
            "strategy"
        ] = strategy

    if (
        "details" in event_fields
        and details is not None
    ):
        event_payload[
            "details"
        ] = details

    event = RecoveryEvent(
        **event_payload
    )

    event_store.setdefault(
        payment_id,
        [],
    ).append(
        event
    )

    return event

# =========================================================
# Event helper
# =========================================================

def record_event(
    *,
    payment_id: UUID,
    event_type: str,
    status: RecoveryStatus | str | None = None,
    recovery_status: RecoveryStatus | str | None = None,
    actor: str = "system",
    metadata: dict[str, Any] | None = None,
    **kwargs,
) -> RecoveryEvent:
    """
    Create and store a recovery lifecycle event.

    This helper normalizes event payloads so that the
    RecoveryEvent schema always receives the required
    `status` field.
    """

    if status is None:
        status = recovery_status

    return _record_recovery_event(
        payment_id=payment_id,
        event_type=event_type,
        status=status,
        metadata=metadata,
        actor=actor,
        **kwargs,
    )


# =========================================================
# Load deterministic simulation data
# =========================================================

def _load_recovery_data() -> None:
    """
    Generate deterministic simulation data and populate all
    runtime stores.

    The function executes only once per application runtime.
    """

    if payments_store:
        return

    recovery_store.clear()
    orders_store.clear()
    customers_store.clear()
    merchants_store.clear()
    idempotency_store.clear()
    event_store.clear()

    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=20,
            customers_per_merchant=100,
            orders_per_customer=5,
        )
    )

    # -----------------------------------------------------
    # Store merchants
    # -----------------------------------------------------

    for merchant in result.merchants:
        merchants_store[
            merchant.merchant_id
        ] = merchant

    # -----------------------------------------------------
    # Store customers
    # -----------------------------------------------------

    for customer in result.customers:
        customers_store[
            customer.customer_id
        ] = customer

    # -----------------------------------------------------
    # Store orders
    # -----------------------------------------------------

    for order in result.orders:
        orders_store[
            order.order_id
        ] = order

    # -----------------------------------------------------
    # Store payments
    # -----------------------------------------------------

    for payment in result.payments:

        payments_store[
            payment.payment_id
        ] = payment

        record_event(
            payment_id=payment.payment_id,
            event_type="payment_created",
            metadata={
                "amount": str(payment.amount),
                "currency": payment.currency,
                "method": (
                    payment.method.value
                    if hasattr(
                        payment.method,
                        "value",
                    )
                    else str(payment.method)
                ),
                "attempt_number": (
                    payment.attempt_number
                ),
            },
        )

        # Payment succeeded
        if payment.failure_code is None:

            record_event(
                payment_id=payment.payment_id,
                event_type="payment_succeeded",
                metadata={
                    "status": (
                        payment.status.value
                        if hasattr(
                            payment.status,
                            "value",
                        )
                        else str(payment.status)
                    ),
                },
            )

        # Payment failed
        else:

            record_event(
                payment_id=payment.payment_id,
                event_type="payment_failed",
                metadata={
                    "failure_code": (
                        payment.failure_code
                    ),
                    "status": (
                        payment.status.value
                        if hasattr(
                            payment.status,
                            "value",
                        )
                        else str(payment.status)
                    ),
                },
            )

    # -----------------------------------------------------
    # Build recovery recommendations
    # -----------------------------------------------------

    for payment in result.payments:

        if payment.failure_code is None:
            continue

        attempt = engine.propose(
            payment
        )

        if attempt is None:
            continue

        recovery_store[
            payment.payment_id
        ] = attempt

        record_event(
            payment_id=payment.payment_id,
            recovery_id=attempt.recovery_id,
            event_type="recovery_proposed",
            metadata={
                "strategy": (
                    attempt.strategy.value
                ),
                "predicted_probability": (
                    attempt.predicted_probability
                ),
                "predicted_revenue": str(
                    attempt.predicted_revenue
                ),
                "decision_score": (
                    attempt.decision_score
                ),
                "reason": (
                    attempt.reason
                ),
            },
        )

def _get_idempotency_key(
    action: str,
    payment_id: UUID,
) -> str:
    """
    Create a deterministic idempotency key for a recovery action.
    """

    return f"{action}:{payment_id}"

def _get_idempotent_response(
    key: str,
) -> dict | None:
    """
    Return the previously stored response for an action,
    if the same action was already processed.
    """

    return idempotency_store.get(key)

def _store_idempotent_response(
    key: str,
    response: dict,
) -> None:
    """
    Store the response of a completed recovery action.
    """

    idempotency_store[key] = response

# =========================================================
# Incident helper
# =========================================================

def _build_incident() -> IncidentAnalysis:
    """
    Build deterministic incident context used by
    counterfactual analysis.
    """

    failed_payments = [
        payment
        for payment
        in payments_store.values()
        if payment.failure_code is not None
    ]

    affected_volume = sum(
        (
            payment.amount
            for payment
            in failed_payments
        ),
        start=Decimal("0"),
    )

    return IncidentAnalysis(
        detected=False,
        severity="normal",
        affected_payments=len(
            failed_payments
        ),
        affected_volume=affected_volume,
        affected_methods=[],
        affected_merchants=[],
        dominant_failure_codes=[],
        recommended_strategy=(
            RecoveryStrategy.NO_ACTION
        ),
    )


# =========================================================
# Adaptive decision helper
# =========================================================

def _build_adaptive_decision(
    payment: Payment,
) -> dict[str, Any]:
    """
    Build a deterministic and explainable recovery decision.
    """

    attempt = recovery_store.get(
        payment.payment_id
    )

    # -----------------------------------------------------
    # Successful payment
    # -----------------------------------------------------

    if payment.failure_code is None:

        return {
            "payment_id": str(
                payment.payment_id
            ),
            "strategy": (
                RecoveryStrategy.NO_ACTION.value
            ),
            "confidence": 1.0,
            "priority_score": 0.0,
            "predicted_probability": 0.0,
            "predicted_revenue": "0",
            "timing": "none",
            "explanation": (
                "Payment completed successfully; "
                "no recovery action is required."
            ),
            "signals": [
                "payment_successful",
            ],
        }

    # -----------------------------------------------------
    # Base recommendation
    # -----------------------------------------------------

    if attempt is not None:

        strategy = attempt.strategy

        probability = float(
            attempt.predicted_probability
        )

        predicted_revenue = (
            attempt.predicted_revenue
        )

        reason = attempt.reason

    else:

        strategy = (
            RecoveryStrategy.NO_ACTION
        )

        probability = 0.0

        predicted_revenue = Decimal("0")

        reason = (
            "No recovery strategy is available."
        )

    failure_code = (
        payment.failure_code.lower()
        if payment.failure_code
        else ""
    )

    signals: list[str] = []

    retryable_failures = {
        "bank_timeout",
        "gateway_timeout",
        "network_error",
    }

    customer_action_failures = {
        "insufficient_funds",
        "authentication_failed",
        "payment_declined",
    }

    # -----------------------------------------------------
    # Failure signals
    # -----------------------------------------------------

    if failure_code in retryable_failures:

        signals.append(
            "transient_failure"
        )

    if failure_code in customer_action_failures:

        signals.append(
            "customer_action_required"
        )

    signals.append(
        f"failure:{failure_code}"
    )

    # -----------------------------------------------------
    # Value signals
    # -----------------------------------------------------

    amount = float(
        payment.amount
    )

    if amount >= 10000:

        signals.append(
            "high_value_payment"
        )

    elif amount >= 5000:

        signals.append(
            "medium_value_payment"
        )

    else:

        signals.append(
            "standard_value_payment"
        )

    # -----------------------------------------------------
    # Attempt signal
    # -----------------------------------------------------

    if payment.attempt_number > 1:

        signals.append(
            "repeat_payment_attempt"
        )

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    confidence = probability

    if failure_code in retryable_failures:

        confidence += 0.05

    if failure_code in customer_action_failures:

        confidence -= 0.03

    if payment.attempt_number > 1:

        confidence -= 0.02

    confidence = max(
        0.0,
        min(
            1.0,
            confidence,
        ),
    )

    # -----------------------------------------------------
    # Priority
    # -----------------------------------------------------

    value_factor = min(
        amount / 10000,
        1.0,
    )

    priority_score = (
        (confidence * 0.60)
        + (value_factor * 0.25)
        + (
            0.15
            if failure_code
            in retryable_failures
            else 0.0
        )
    )

    priority_score = max(
        0.0,
        min(
            1.0,
            priority_score,
        ),
    )

    # -----------------------------------------------------
    # Timing
    # -----------------------------------------------------

    if failure_code in retryable_failures:

        timing = "immediate"

    elif failure_code == "insufficient_funds":

        timing = "later"

    elif failure_code in {
        "authentication_failed",
        "payment_declined",
    }:

        timing = "immediate"

    else:

        timing = "recommended"

    explanation = reason

    if not explanation:

        explanation = (
            f"{failure_code.replace('_', ' ').title()} "
            "identified as the primary recovery signal."
        )

    strategy_value = (
        strategy.value
        if hasattr(
            strategy,
            "value",
        )
        else str(strategy)
    )

    return {
        "payment_id": str(
            payment.payment_id
        ),
        "strategy": strategy_value,
        "confidence": round(
            confidence,
            4,
        ),
        "priority_score": round(
            priority_score,
            4,
        ),
        "predicted_probability": round(
            probability,
            4,
        ),
        "predicted_revenue": str(
            predicted_revenue
        ),
        "timing": timing,
        "explanation": explanation,
        "signals": signals,
    }

# =========================================================
# Recovery Priority Scoring
# =========================================================

# =========================================================
# Recovery Priority Scoring
# =========================================================

def _calculate_recovery_priority(
    payment: Payment,
    attempt: Any,
) -> dict[str, Any]:
    """
    Calculate a deterministic and explainable recovery priority.

    Priority score:
        0 - 40  -> payment amount
        0 - 40  -> recovery probability
        0 - 20  -> attempt urgency

    Total:
        0 - 100
    """

    # =================================================
    # Safe payment amount
    # =================================================

    raw_amount = getattr(
        payment,
        "amount",
        0,
    )

    try:
        amount = float(
            raw_amount
            if raw_amount is not None
            else 0
        )
    except (
        TypeError,
        ValueError,
    ):
        amount = 0.0

    amount = max(
        0.0,
        amount,
    )

    # =================================================
    # Safe recovery probability
    # =================================================

    probability = 0.0

    probability_fields = [
        "predicted_probability",
        "recovery_probability",
        "success_probability",
        "probability",
    ]

    for field_name in probability_fields:

        value = getattr(
            attempt,
            field_name,
            None,
        )

        if value is None:
            continue

        try:

            probability = float(
                value
            )

            break

        except (
            TypeError,
            ValueError,
        ):

            continue

    # Support percentages such as 80 -> 0.80

    if probability > 1.0:

        probability = (
            probability / 100.0
        )

    probability = max(
        0.0,
        min(
            probability,
            1.0,
        ),
    )

    # =================================================
    # Safe attempt number
    # =================================================

    raw_attempt_number = getattr(
        payment,
        "attempt_number",
        1,
    )

    try:

        attempt_number = int(
            raw_attempt_number
            if raw_attempt_number is not None
            else 1
        )

    except (
        TypeError,
        ValueError,
    ):

        attempt_number = 1

    attempt_number = max(
        1,
        attempt_number,
    )

    # =================================================
    # Revenue score
    #
    # Maximum contribution: 40
    # Amount of 10,000+ receives full score.
    # =================================================

    revenue_score = min(
        (
            amount / 10000.0
        )
        * 40.0,
        40.0,
    )

    # =================================================
    # Probability score
    #
    # Maximum contribution: 40
    # =================================================

    probability_score = (
        probability
        * 40.0
    )

    # =================================================
    # Urgency score
    #
    # More attempts generally indicate greater urgency.
    # Maximum contribution: 20.
    # =================================================

    urgency_score = min(
        (
            attempt_number - 1
        )
        * 5.0,
        20.0,
    )

    # =================================================
    # Final priority
    # =================================================

    priority_score = (
        revenue_score
        + probability_score
        + urgency_score
    )

    priority_score = max(
        0.0,
        min(
            priority_score,
            100.0,
        ),
    )

    # =================================================
    # Expected recoverable revenue
    # =================================================

    expected_revenue = (
        amount
        * probability
    )

    # =================================================
    # Priority classification
    # =================================================

    if priority_score >= 75:

        priority_level = "critical"

    elif priority_score >= 50:

        priority_level = "high"

    elif priority_score >= 25:

        priority_level = "medium"

    else:

        priority_level = "low"

    # =================================================
    # Response
    # =================================================

    return {
        "priority_score": round(
            priority_score,
            2,
        ),
        "priority_level": (
            priority_level
        ),
        "expected_revenue": round(
            expected_revenue,
            2,
        ),
        "recovery_probability": round(
            probability,
            4,
        ),
        "score_breakdown": {
            "revenue_score": round(
                revenue_score,
                2,
            ),
            "probability_score": round(
                probability_score,
                2,
            ),
            "urgency_score": round(
                urgency_score,
                2,
            ),
        },
    }

# =========================================================
# GET /recovery/recommendations
# =========================================================

@router.get(
    "/recommendations"
)
def get_recommendations():

    _load_recovery_data()

    return [
        attempt.model_dump(
            mode="json"
        )
        for attempt
        in recovery_store.values()
        if (
            attempt.status
            == RecoveryStatus.PROPOSED
        )
    ]


# =========================================================
# GET /recovery/payments
# =========================================================

@router.get(
    "/payments"
)
def get_payments(
    search: str | None = None,
    status: str | None = None,
    method: str | None = None,
    failure_code: str | None = None,
    limit: int = 100,
):

    _load_recovery_data()

    limit = max(
        1,
        min(
            limit,
            500,
        ),
    )

    search_value = (
        search.strip().lower()
        if search
        else None
    )

    status_value = (
        status.strip().lower()
        if status
        else None
    )

    method_value = (
        method.strip().lower()
        if method
        else None
    )

    failure_value = (
        failure_code.strip().lower()
        if failure_code
        else None
    )

    response_payments = []

    for payment in (
        payments_store.values()
    ):

        payment_status = (
            payment.status.value
            if hasattr(
                payment.status,
                "value",
            )
            else str(payment.status)
        )

        payment_method = (
            payment.method.value
            if hasattr(
                payment.method,
                "value",
            )
            else str(payment.method)
        )

        payment_failure = (
            payment.failure_code.lower()
            if payment.failure_code
            else None
        )

        # Filters

        if (
            status_value
            and payment_status.lower()
            != status_value
        ):
            continue

        if (
            method_value
            and payment_method.lower()
            != method_value
        ):
            continue

        if (
            failure_value
            and payment_failure
            != failure_value
        ):
            continue

        order = orders_store.get(
            payment.order_id
        )

        customer = customers_store.get(
            payment.customer_id
        )

        # Search

        if search_value:

            merchant_id_text = (
                str(order.merchant_id)
                if order
                else ""
            )

            searchable = " ".join(
                [
                    str(
                        payment.payment_id
                    ),
                    str(
                        payment.order_id
                    ),
                    str(
                        payment.customer_id
                    ),
                    merchant_id_text,
                    payment_method,
                    payment_status,
                    payment_failure or "",
                ]
            ).lower()

            if (
                search_value
                not in searchable
            ):
                continue

        merchant_id = (
            order.merchant_id
            if order
            else None
        )

        recovery = recovery_store.get(
            payment.payment_id
        )

        response_payments.append(
            {
                "payment_id": str(
                    payment.payment_id
                ),
                "order_id": str(
                    payment.order_id
                ),
                "customer_id": str(
                    payment.customer_id
                ),
                "merchant_id": (
                    str(merchant_id)
                    if merchant_id
                    else None
                ),
                "amount": str(
                    payment.amount
                ),
                "currency": (
                    payment.currency
                ),
                "method": (
                    payment_method
                ),
                "status": (
                    payment_status
                ),
                "failure_code": (
                    payment.failure_code
                ),
                "attempt_number": (
                    payment.attempt_number
                ),
                "created_at": (
                    payment.created_at.isoformat()
                ),
                "updated_at": (
                    payment.updated_at.isoformat()
                ),
                "customer_segment": (
                    customer.customer_segment
                    if customer
                    else None
                ),
                "recovery": (
                    recovery.model_dump(
                        mode="json"
                    )
                    if recovery
                    else None
                ),
            }
        )

    response_payments.sort(
        key=lambda item: (
            item["created_at"]
        ),
        reverse=True,
    )

    return {
        "payments": (
            response_payments[:limit]
        ),
        "total": len(
            response_payments
        ),
        "filters": {
            "search": search,
            "status": status,
            "method": method,
            "failure_code": failure_code,
        },
    }


# =========================================================
# GET /recovery/payments/{payment_id}
# =========================================================

@router.get(
    "/payments/{payment_id}"
)
def get_payment_details(
    payment_id: UUID,
):

    _load_recovery_data()

    payment = payments_store.get(
        payment_id
    )

    if payment is None:

        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    order = orders_store.get(
        payment.order_id
    )

    customer = customers_store.get(
        payment.customer_id
    )

    merchant = (
        merchants_store.get(
            order.merchant_id
        )
        if order
        else None
    )

    recovery = recovery_store.get(
        payment_id
    )

    return {
        "payment": (
            payment.model_dump(
                mode="json"
            )
        ),
        "order": (
            order.model_dump(
                mode="json"
            )
            if order
            else None
        ),
        "customer": (
            customer.model_dump(
                mode="json"
            )
            if customer
            else None
        ),
        "merchant": (
            merchant.model_dump(
                mode="json"
            )
            if merchant
            else None
        ),
        "recovery": (
            recovery.model_dump(
                mode="json"
            )
            if recovery
            else None
        ),
    }

# =========================================================
# GET /recovery/analytics/summary
# =========================================================

@router.get(
    "/analytics/summary"
)
def get_recovery_analytics_summary():
    """
    Return a high-level operational summary of payment
    failures and recovery performance.
    """

    _load_recovery_data()

    # -----------------------------------------------------
    # Payment metrics
    # -----------------------------------------------------

    total_payments = len(
        payments_store
    )

    failed_payments = [
        payment
        for payment
        in payments_store.values()
        if payment.failure_code is not None
    ]

    failed_payment_count = len(
        failed_payments
    )

    successful_payments = [
        payment
        for payment
        in payments_store.values()
        if payment.failure_code is None
    ]

    successful_payment_count = len(
        successful_payments
    )

    failure_rate = (
        failed_payment_count
        / total_payments
        if total_payments > 0
        else 0.0
    )

    failed_payment_volume = sum(
        (
            payment.amount
            for payment
            in failed_payments
        ),
        start=Decimal("0"),
    )

    total_payment_volume = sum(
        (
            payment.amount
            for payment
            in payments_store.values()
        ),
        start=Decimal("0"),
    )

    # -----------------------------------------------------
    # Recovery metrics
    # -----------------------------------------------------

    recovery_attempts = list(
        recovery_store.values()
    )

    recovery_candidates = len(
        recovery_attempts
    )

    proposed_recoveries = [
        attempt
        for attempt
        in recovery_attempts
        if attempt.status
        == RecoveryStatus.PROPOSED
    ]

    approved_recoveries = [
        attempt
        for attempt
        in recovery_attempts
        if attempt.status
        == RecoveryStatus.APPROVED
    ]

    executing_recoveries = [
        attempt
        for attempt
        in recovery_attempts
        if (
            getattr(
                RecoveryStatus,
                "EXECUTING",
                None,
            )
            is not None
            and attempt.status
            == RecoveryStatus.EXECUTING
        )
    ]

    successful_recoveries = [
        attempt
        for attempt
        in recovery_attempts
        if attempt.status
        == RecoveryStatus.SUCCEEDED
    ]

    failed_recoveries = [
        attempt
        for attempt
        in recovery_attempts
        if attempt.status
        == RecoveryStatus.FAILED
    ]

    completed_recoveries = (
        len(successful_recoveries)
        + len(failed_recoveries)
    )

    recovery_success_rate = (
        len(successful_recoveries)
        / completed_recoveries
        if completed_recoveries > 0
        else 0.0
    )

    recovered_revenue = sum(
        (
            attempt.actual_revenue
            or Decimal("0")
            for attempt
            in successful_recoveries
        ),
        start=Decimal("0"),
    )

    predicted_revenue = sum(
        (
            attempt.predicted_revenue
            for attempt
            in recovery_attempts
        ),
        start=Decimal("0"),
    )

    # -----------------------------------------------------
    # Strategy performance
    # -----------------------------------------------------

    strategy_metrics = {}

    for attempt in recovery_attempts:

        strategy = (
            attempt.strategy.value
            if hasattr(
                attempt.strategy,
                "value",
            )
            else str(
                attempt.strategy
            )
        )

        if strategy not in strategy_metrics:

            strategy_metrics[
                strategy
            ] = {
                "strategy": strategy,
                "attempts": 0,
                "successful": 0,
                "failed": 0,
                "predicted_revenue": (
                    Decimal("0")
                ),
                "recovered_revenue": (
                    Decimal("0")
                ),
            }

        metric = strategy_metrics[
            strategy
        ]

        metric["attempts"] += 1

        metric[
            "predicted_revenue"
        ] += attempt.predicted_revenue

        if (
            attempt.status
            == RecoveryStatus.SUCCEEDED
        ):

            metric[
                "successful"
            ] += 1

            metric[
                "recovered_revenue"
            ] += (
                attempt.actual_revenue
                or Decimal("0")
            )

        elif (
            attempt.status
            == RecoveryStatus.FAILED
        ):

            metric[
                "failed"
            ] += 1

    strategy_performance = []

    for metric in (
        strategy_metrics.values()
    ):

        completed = (
            metric["successful"]
            + metric["failed"]
        )

        success_rate = (
            metric["successful"]
            / completed
            if completed > 0
            else 0.0
        )

        strategy_performance.append(
            {
                "strategy": (
                    metric["strategy"]
                ),
                "attempts": (
                    metric["attempts"]
                ),
                "successful": (
                    metric["successful"]
                ),
                "failed": (
                    metric["failed"]
                ),
                "success_rate": round(
                    success_rate,
                    4,
                ),
                "predicted_revenue": str(
                    metric[
                        "predicted_revenue"
                    ]
                ),
                "recovered_revenue": str(
                    metric[
                        "recovered_revenue"
                    ]
                ),
            }
        )

    strategy_performance.sort(
        key=lambda item: (
            item["recovered_revenue"]
        ),
        reverse=True,
    )

    # -----------------------------------------------------
    # Event metrics
    # -----------------------------------------------------

    total_events = sum(
        len(events)
        for events
        in event_store.values()
    )

    event_counts = {}

    for events in (
        event_store.values()
    ):

        for event in events:

            event_type = getattr(
                event,
                "event_type",
                "unknown",
            )

            event_counts[
                event_type
            ] = (
                event_counts.get(
                    event_type,
                    0,
                )
                + 1
            )

    # -----------------------------------------------------
    # Final response
    # -----------------------------------------------------

    return {
        "payments": {
            "total": (
                total_payments
            ),
            "successful": (
                successful_payment_count
            ),
            "failed": (
                failed_payment_count
            ),
            "failure_rate": round(
                failure_rate,
                4,
            ),
            "total_volume": str(
                total_payment_volume
            ),
            "failed_volume": str(
                failed_payment_volume
            ),
        },
        "recovery": {
            "candidates": (
                recovery_candidates
            ),
            "proposed": len(
                proposed_recoveries
            ),
            "approved": len(
                approved_recoveries
            ),
            "executing": len(
                executing_recoveries
            ),
            "successful": len(
                successful_recoveries
            ),
            "failed": len(
                failed_recoveries
            ),
            "completed": (
                completed_recoveries
            ),
            "success_rate": round(
                recovery_success_rate,
                4,
            ),
            "predicted_revenue": str(
                predicted_revenue
            ),
            "recovered_revenue": str(
                recovered_revenue
            ),
        },
        "strategy_performance": (
            strategy_performance
        ),
        "events": {
            "total": total_events,
            "by_type": (
                event_counts
            ),
        },
    }

# =========================================================
# GET /recovery/{payment_id}/decision
# =========================================================

@router.get(
    "/{payment_id}/decision"
)
def get_adaptive_decision(
    payment_id: UUID,
):

    _load_recovery_data()

    payment = payments_store.get(
        payment_id
    )

    if payment is None:

        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    return _build_adaptive_decision(
        payment
    )


# =========================================================
# GET /recovery/{payment_id}/counterfactual
# =========================================================

@router.get(
    "/{payment_id}/counterfactual"
)
def get_counterfactual_analysis(
    payment_id: UUID,
):

    _load_recovery_data()

    payment = payments_store.get(
        payment_id
    )

    if payment is None:

        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.failure_code is None:

        return {
            "payment_id": str(
                payment.payment_id
            ),
            "recommended_strategy": (
                RecoveryStrategy.NO_ACTION.value
            ),
            "options": [],
        }

    incident = _build_incident()

    options = simulate_counterfactuals(
        payment=payment,
        incident=incident,
    )

    return {
        "payment_id": str(
            payment.payment_id
        ),
        "recommended_strategy": (
            options[0].strategy.value
            if options
            else RecoveryStrategy.NO_ACTION.value
        ),
        "options": [
            {
                "strategy": (
                    option.strategy.value
                ),
                "probability": (
                    option.probability
                ),
                "expected_revenue": str(
                    option.expected_revenue
                ),
                "revenue_uplift": str(
                    option.revenue_uplift
                ),
                "relative_uplift": (
                    option.relative_uplift
                ),
                "recommended": (
                    option.recommended
                ),
                "explanation": (
                    option.explanation
                ),
            }
            for option
            in options
        ],
    }


# =========================================================
# GET /recovery/{payment_id}/events
# =========================================================

@router.get(
    "/{payment_id}/events"
)
def get_recovery_events(
    payment_id: UUID,
):

    _load_recovery_data()

    payment = payments_store.get(
        payment_id
    )

    if payment is None:

        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    events = event_store.get(
        payment_id,
        [],
    )

    # Sort only when created_at exists

    events = sorted(
        events,
        key=lambda event: (
            getattr(
                event,
                "created_at",
                None,
            )
            or getattr(
                event,
                "timestamp",
                None,
            )
            or 0
        ),
    )

    return {
        "payment_id": str(
            payment_id
        ),
        "total_events": len(
            events
        ),
        "events": [
            event.model_dump(
                mode="json"
            )
            for event
            in events
        ],
    }


# =========================================================
# GET /recovery/priority-queue
# =========================================================

@router.get("/priority-queue")
def get_recovery_priority_queue(
    limit: int = 50,
):
    """
    Return actionable recovery attempts ranked
    by business priority.
    """

    _load_recovery_data()

    limit = max(
        1,
        min(
            limit,
            500,
        ),
    )

    priority_queue = []

    for payment_id, attempt in (
        recovery_store.items()
    ):

        payment = payments_store.get(
            payment_id,
        )

        if payment is None:
            continue

        # ---------------------------------------------
        # Safe recovery status extraction
        # ---------------------------------------------

        attempt_status = getattr(
            attempt,
            "status",
            None,
        )

        attempt_status_value = (
            attempt_status.value
            if hasattr(
                attempt_status,
                "value",
            )
            else str(
                attempt_status
            )
        )

        # Only actionable recovery attempts

        actionable_statuses = {
            RecoveryStatus.PROPOSED.value,
            RecoveryStatus.APPROVED.value,
        }

        if (
            attempt_status_value
            not in actionable_statuses
        ):
            continue

        # ---------------------------------------------
        # Calculate priority
        # ---------------------------------------------

        priority = (
            _calculate_recovery_priority(
                payment,
                attempt,
            )
        )

        # ---------------------------------------------
        # Safe strategy extraction
        # ---------------------------------------------

        strategy = getattr(
            attempt,
            "strategy",
            None,
        )

        strategy_value = (
            strategy.value
            if hasattr(
                strategy,
                "value",
            )
            else (
                str(strategy)
                if strategy is not None
                else None
            )
        )

        # ---------------------------------------------
        # Safe payment fields
        # ---------------------------------------------

        payment_status = getattr(
            payment,
            "status",
            None,
        )

        payment_status_value = (
            payment_status.value
            if hasattr(
                payment_status,
                "value",
            )
            else str(
                payment_status
            )
        )

        priority_queue.append(
            {
                "payment_id": str(
                    getattr(
                        payment,
                        "payment_id",
                        payment_id,
                    )
                ),
                "order_id": str(
                    getattr(
                        payment,
                        "order_id",
                        "",
                    )
                ),
                "customer_id": str(
                    getattr(
                        payment,
                        "customer_id",
                        "",
                    )
                ),
                "amount": str(
                    getattr(
                        payment,
                        "amount",
                        0,
                    )
                ),
                "currency": getattr(
                    payment,
                    "currency",
                    None,
                ),
                "payment_status": (
                    payment_status_value
                ),
                "failure_code": getattr(
                    payment,
                    "failure_code",
                    None,
                ),
                "attempt_number": getattr(
                    payment,
                    "attempt_number",
                    1,
                ),
                "recovery_status": (
                    attempt_status_value
                ),
                "strategy": (
                    strategy_value
                ),
                **priority,
            }
        )

    # -------------------------------------------------
    # Sort highest priority first
    # -------------------------------------------------

    priority_queue.sort(
        key=lambda item: (
            item[
                "priority_score"
            ],
            item[
                "expected_revenue"
            ],
        ),
        reverse=True,
    )

    return {
        "total": len(
            priority_queue
        ),
        "limit": limit,
        "queue": (
            priority_queue[:limit]
        ),
    }

# =========================================================
# GET /recovery/{payment_id}
# =========================================================

@router.get(
    "/{payment_id}"
)
def get_recovery(
    payment_id: UUID,
):

    _load_recovery_data()

    attempt = recovery_store.get(
        payment_id
    )

    if attempt is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Recovery recommendation "
                "not found"
            ),
        )

    return attempt.model_dump(
        mode="json"
    )


# =========================================================
# POST /recovery/{payment_id}/approve
# =========================================================

@router.post("/{payment_id}/approve")
def approve_recovery(payment_id: UUID):
    """
    Approve a proposed recovery attempt.

    Duplicate approval requests return the previous
    response instead of processing the approval twice.
    """

    _load_recovery_data()

    # -------------------------------------------------
    # Idempotency check
    # -------------------------------------------------

    idempotency_key = _get_idempotency_key(
        "approve",
        payment_id,
    )

    previous_response = _get_idempotent_response(
        idempotency_key,
    )

    if previous_response is not None:
        return {
            **previous_response,
            "idempotent_replay": True,
        }

    # -------------------------------------------------
    # Payment lookup
    # -------------------------------------------------

    payment = payments_store.get(
        payment_id,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    # -------------------------------------------------
    # Recovery lookup
    # -------------------------------------------------

    attempt = recovery_store.get(
        payment_id,
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery recommendation not found",
        )

    # -------------------------------------------------
    # Validate recovery status
    # -------------------------------------------------

    if attempt.status == RecoveryStatus.APPROVED:

        response = attempt.model_dump(
            mode="json",
        )

        response["idempotent_replay"] = False

        _store_idempotent_response(
            idempotency_key,
            response,
        )

        return response

    if attempt.status != RecoveryStatus.PROPOSED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only proposed recovery attempts "
                "can be approved."
            ),
        )

    # -------------------------------------------------
    # Update recovery state
    # -------------------------------------------------

    try:
        transition_recovery(
            attempt,
            RecoveryStatus.APPROVED,
            actor="recovery_api",
        )

    except InvalidRecoveryTransition as exc:
        raise HTTPException(
            status_code=400,
            detail=str(
                exc
            ),
        ) from exc

    recovery_store[
        payment_id
    ] = attempt

    # -------------------------------------------------
    # Record lifecycle event
    # -------------------------------------------------

    _record_recovery_event(
        payment_id=payment_id,
        event_type="recovery_approved",
        status=RecoveryStatus.APPROVED.value,
        data={
            "strategy": (
                attempt.strategy.value
            ),
        },
    )

    # -------------------------------------------------
    # Build response
    # -------------------------------------------------

    response = attempt.model_dump(
        mode="json",
    )

    response["idempotent_replay"] = False

    # -------------------------------------------------
    # Store idempotent response
    # -------------------------------------------------

    _store_idempotent_response(
        idempotency_key,
        response,
    )

    return response


@router.post("/{payment_id}/execute")
def execute_recovery(
    payment_id: UUID,
):
    """
    Execute an approved recovery attempt.
    """

    recovery = recovery_store.get(payment_id)

    if recovery is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery attempt not found",
        )

    payment = payments_store.get(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    try:
        current_status = RecoveryStatus(
            recovery.status
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown recovery status: {recovery.status}",
        ) from exc

    if current_status != RecoveryStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Recovery must be approved before execution.",
        )

    executor = RecoveryExecutor()

    try:
        updated_recovery = executor.execute(
            attempt=recovery,
            payment=payment,
            rng=random_generator,
        )

    except InvalidRecoveryTransition as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    recovery_store[payment_id] = updated_recovery

    return updated_recovery
