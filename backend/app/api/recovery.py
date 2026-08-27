from random import Random
from uuid import UUID

from fastapi import APIRouter, HTTPException

from backend.app.domain.enums import RecoveryStatus, RecoveryStrategy
from backend.app.domain.models import Payment
from simulator.analytics.incident_analysis import IncidentAnalysis
from simulator.recovery.engine import RecoveryEngine
from simulator.recovery.executor import RecoveryExecutor
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


router = APIRouter(
    prefix="/recovery",
    tags=["Recovery"],
)


# =========================================================
# Runtime stores
# =========================================================

payments_store: dict[UUID, Payment] = {}
recovery_store = {}

engine = RecoveryEngine()
executor = RecoveryExecutor()


# =========================================================
# Generate deterministic recovery data
# =========================================================

def _load_recovery_data() -> None:
    """
    Generate a deterministic simulation and populate the
    runtime recovery stores.
    """

    if recovery_store:
        return

    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=20,
            customers_per_merchant=100,
            orders_per_customer=5,
        )
    )

    for payment in result.payments:
        payments_store[payment.payment_id] = payment

    failed_payments = [
        payment
        for payment in result.payments
        if payment.failure_code is not None
    ]

    incident = IncidentAnalysis(
        detected=False,
        severity="normal",
        affected_payments=len(failed_payments),
        affected_volume=sum(
            (
                payment.amount
                for payment in failed_payments
            ),
            start=0,
        ),
        affected_methods=[],
        affected_merchants=[],
        dominant_failure_codes=[],
        recommended_strategy=RecoveryStrategy.NO_ACTION,
    )

    failed_payment_list = [
        payment
        for payment in result.payments
        if payment.failure_code is not None
    ]

    for payment in failed_payment_list:
        attempt = engine.propose(payment)

        if attempt is None:
            continue

        recovery_store[payment.payment_id] = attempt


# =========================================================
# GET /recovery/recommendations
# =========================================================

@router.get("/recommendations")
def get_recommendations():
    """
    Return all currently proposed recovery attempts.
    """

    _load_recovery_data()

    return [
        attempt.model_dump(mode="json")
        for attempt in recovery_store.values()
        if attempt.status == RecoveryStatus.PROPOSED
    ]


# =========================================================
# GET /recovery/{payment_id}
# =========================================================

@router.get("/{payment_id}")
def get_recovery(payment_id: UUID):
    """
    Return the current recovery attempt for a payment.
    """

    _load_recovery_data()

    attempt = recovery_store.get(payment_id)

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery recommendation not found",
        )

    return attempt.model_dump(mode="json")


# =========================================================
# POST /recovery/{payment_id}/approve
# =========================================================

@router.post("/{payment_id}/approve")
def approve_recovery(payment_id: UUID):
    """
    Approve a proposed recovery attempt.
    """

    _load_recovery_data()

    attempt = recovery_store.get(payment_id)

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery recommendation not found",
        )

    if attempt.status != RecoveryStatus.PROPOSED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only proposed recovery attempts "
                "can be approved."
            ),
        )

    attempt.status = RecoveryStatus.APPROVED

    return {
        "payment_id": str(payment_id),
        "status": attempt.status.value,
        "strategy": attempt.strategy.value,
        "predicted_probability": (
            attempt.predicted_probability
        ),
        "predicted_revenue": (
            attempt.predicted_revenue
        ),
    }


# =========================================================
# POST /recovery/{payment_id}/execute
# =========================================================

@router.post("/{payment_id}/execute")
def execute_recovery(payment_id: UUID):
    """
    Execute an approved recovery attempt.
    """

    _load_recovery_data()

    attempt = recovery_store.get(payment_id)

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Recovery recommendation not found",
        )

    payment = payments_store.get(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if attempt.status != RecoveryStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Recovery must be approved "
                "before execution."
            ),
        )

    result = executor.execute(
        attempt=attempt,
        payment=payment,
        rng=Random(42),
    )

    return result.model_dump(mode="json")