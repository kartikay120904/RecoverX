"""
RecoverX FastAPI application.

Provides:
- Health endpoint
- Simulation endpoints
- Analytics endpoints
- Recovery endpoints
- Razorpay TEST MODE payment endpoints
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.api.recovery import router as recovery_router
from backend.app.services.razorpay_service import razorpay_service
from simulator.analytics.report import build_simulation_report
from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


# =========================================================
# FastAPI application
# =========================================================

app = FastAPI(
    title="RecoverX API",
    description=(
        "Payment recovery intelligence platform with "
        "simulation, analytics, recovery automation, "
        "and Razorpay Test Mode integration."
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Existing Recovery API
# =========================================================

app.include_router(recovery_router)


# =========================================================
# Health
# =========================================================

@app.get("/health")
def health() -> dict[str, str]:
    """
    Health check endpoint.
    """
    return {
        "status": "ok",
        "service": "recoverx",
    }


# =========================================================
# Simulation
# =========================================================

class SimulationRequest(BaseModel):
    seed: int = 42
    merchant_count: int = 20
    customers_per_merchant: int = 100
    orders_per_customer: int = 5


@app.post("/simulation/run")
def simulation_run(request: SimulationRequest) -> dict[str, Any]:
    """
    Run a deterministic RecoverX payment simulation.
    """

    config = SimulationRunConfig(
        seed=request.seed,
        merchant_count=request.merchant_count,
        customers_per_merchant=request.customers_per_merchant,
        orders_per_customer=request.orders_per_customer,
    )

    result = run_simulation(config)

    return {
    "merchants": request.merchant_count,
    "customers": request.merchant_count * request.customers_per_merchant,
    "orders": (
        request.merchant_count
        * request.customers_per_merchant
        * request.orders_per_customer
    ),
    "payments": len(result.payments),
    "events": len(result.events),
    "recovery_attempts": len(result.recovery_attempts),
}


# =========================================================
# Analytics
# =========================================================

@app.post("/analytics/report")
def analytics_report(request: SimulationRequest) -> dict[str, Any]:
    config = SimulationRunConfig(
        seed=request.seed,
        merchant_count=request.merchant_count,
        customers_per_merchant=request.customers_per_merchant,
        orders_per_customer=request.orders_per_customer,
    )

    result = run_simulation(config)

    report = build_simulation_report(
        payments=result.payments,
        orders=result.orders,
        customers=result.customers,
        merchants=result.merchants,
    )

    return {
        "metrics": (
            report.payment_metrics.model_dump(mode="json")
            if hasattr(report.payment_metrics, "model_dump")
            else report.payment_metrics
        ),
        "success_rate_by_method": report.success_rate_by_method,
        "failure_code_distribution": report.failure_code_distribution,
        "failure_rate_by_merchant": report.failure_rate_by_merchant,
        "failure_rate_by_customer_segment": (
            report.failure_rate_by_customer_segment
        ),
        "anomalies": [
            anomaly.model_dump(mode="json")
            if hasattr(anomaly, "model_dump")
            else anomaly
            for anomaly in report.anomalies
        ],
        "incident": (
            report.incident.model_dump(mode="json")
            if hasattr(report.incident, "model_dump")
            else report.incident
        ),
        "recovery_recommendations": [
            recommendation.model_dump(mode="json")
            if hasattr(recommendation, "model_dump")
            else recommendation
            for recommendation in report.recovery_recommendations
        ],
        "total_recovery_recommendations": (
            report.total_recovery_recommendations
        ),
        "predicted_recovery_revenue": str(
            report.predicted_recovery_revenue
        ),
    }
# =========================================================
# Razorpay TEST MODE
# =========================================================

class RazorpayOrderRequest(BaseModel):
    """
    Request for creating a Razorpay order.

    Amount is expressed in the smallest currency unit.

    Example:
        ₹10 = 1000 paise
    """

    amount: int
    currency: str = "INR"
    receipt: str | None = None


class RazorpayVerifyRequest(BaseModel):
    """
    Razorpay Checkout verification payload.
    """

    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# =========================================================
# Razorpay configuration
# =========================================================

@app.get("/razorpay/config")
def razorpay_config() -> dict[str, str]:
    """
    Return the public Razorpay TEST MODE key.

    IMPORTANT:
    The Razorpay secret is NEVER returned to the frontend.
    """

    return {
        "key_id": razorpay_service.key_id,
        "mode": "test",
    }


# =========================================================
# Create Razorpay order
# =========================================================

@app.post("/razorpay/order")
def create_razorpay_order(
    request: RazorpayOrderRequest,
) -> dict[str, Any]:
    """
    Create a Razorpay TEST MODE order.
    """

    if request.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero.",
        )

    if request.currency.upper() != "INR":
        raise HTTPException(
            status_code=400,
            detail="RecoverX currently supports INR only.",
        )

    try:
        order = razorpay_service.create_order(
            amount=request.amount,
            currency=request.currency.upper(),
            receipt=request.receipt,
        )

        return {
            "success": True,
            "mode": "test",
            "order": order,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to create Razorpay order: {exc}",
        ) from exc


# =========================================================
# Verify Razorpay payment
# =========================================================

@app.post("/razorpay/verify")
def verify_razorpay_payment(
    request: RazorpayVerifyRequest,
) -> dict[str, Any]:
    """
    Verify a Razorpay Checkout payment signature.

    The signature is verified server-side using the
    Razorpay secret stored in backend/.env.
    """

    try:
        verified = razorpay_service.verify_payment_signature(
            razorpay_order_id=request.razorpay_order_id,
            razorpay_payment_id=request.razorpay_payment_id,
            razorpay_signature=request.razorpay_signature,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Payment verification failed: {exc}",
        ) from exc

    if not verified:
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay payment signature.",
        )

    return {
        "success": True,
        "verified": True,
        "mode": "test",
        "order_id": request.razorpay_order_id,
        "payment_id": request.razorpay_payment_id,
    }


# =========================================================
# Razorpay order lookup
# =========================================================

@app.get("/razorpay/order/{order_id}")
def get_razorpay_order(
    order_id: str,
) -> dict[str, Any]:
    """
    Fetch a Razorpay order from TEST MODE.
    """

    try:
        order = razorpay_service.fetch_order(order_id)

        return {
            "success": True,
            "mode": "test",
            "order": order,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to fetch Razorpay order: {exc}",
        ) from exc


# =========================================================
# Razorpay payment lookup
# =========================================================

@app.get("/razorpay/payment/{payment_id}")
def get_razorpay_payment(
    payment_id: str,
) -> dict[str, Any]:
    """
    Fetch a Razorpay payment from TEST MODE.
    """

    try:
        payment = razorpay_service.fetch_payment(payment_id)

        return {
            "success": True,
            "mode": "test",
            "payment": payment,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to fetch Razorpay payment: {exc}",
        ) from exc