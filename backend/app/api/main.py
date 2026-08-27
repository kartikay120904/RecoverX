from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.domain.enums import RecoveryStatus
from decimal import Decimal

from simulator.runner import run_simulation
from simulator.analytics.comparison import compare_simulations
from simulator.simulation_config import SimulationRunConfig
from simulator.analytics.payment_metrics import (
    calculate_payment_metrics,
    success_rate_by_method,
    failure_code_distribution,
    failure_rate_by_merchant,
    failure_rate_by_customer_segment,
)
from uuid import UUID

from fastapi import HTTPException

from backend.app.domain.models import Payment
from simulator.analytics.counterfactual import (
    simulate_counterfactuals,
)
from simulator.analytics.anomaly_detection import detect_anomalies
from simulator.analytics.incident_analysis import analyze_incident
from simulator.analytics.recovery_recommendation import (
    recommend_recoveries,
)
from backend.app.api.schemas import (
    AnalyticsReportResponse,
    HealthResponse,
    SimulationResponse,
)

from backend.app.api.recovery import router as recovery_router
from simulator.analytics.adaptive_recovery import (
    rank_adaptive_recoveries,
    decision_to_dict,
)

app = FastAPI(
    title="RecoverX API",
    description="Payment failure recovery and analytics platform",
    version="1.0.0",
)
app.include_router(recovery_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/simulation/run",
    response_model=SimulationResponse,
)
def run_simulation_api(
    config: SimulationRunConfig | None = None,
):
    result = run_simulation(config)

    return {
        "merchants": len(result.merchants),
        "customers": len(result.customers),
        "orders": len(result.orders),
        "payments": len(result.payments),
        "events": len(result.events),
        "recovery_attempts": len(result.recovery_attempts),
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "ok",
        "service": "recoverx",
    }


@app.post("/simulation/compare")
def compare_simulation_api(
    baseline_config: SimulationRunConfig | None = None,
    incident_config: SimulationRunConfig | None = None,
):
    baseline = run_simulation(baseline_config)
    incident = run_simulation(incident_config)

    comparison = compare_simulations(
        baseline,
        incident,
    )

    return {
        "baseline": {
            "failure_rate": comparison.baseline_failure_rate,
            "failed_payments": comparison.baseline_failed_payments,
            "failed_volume": str(
                comparison.baseline_failed_volume
            ),
        },
        "incident": {
            "failure_rate": comparison.incident_failure_rate,
            "failed_payments": comparison.incident_failed_payments,
            "failed_volume": str(
                comparison.incident_failed_volume
            ),
        },
        "impact": {
            "failure_rate_delta": comparison.failure_rate_delta,
            "failed_payments_delta": comparison.failed_payments_delta,
            "failed_volume_delta": str(
                comparison.failed_volume_delta
            ),
        },
    }

@app.post(
    "/analytics/report",
    response_model=AnalyticsReportResponse,
)
def analytics_report_api(
    config: SimulationRunConfig | None = None,
    failure_rate_threshold: float = 0.10,
    failure_code_threshold: float = 0.40,
):
    result = run_simulation(config)

    metrics = calculate_payment_metrics(result.payments)

    anomalies = detect_anomalies(
        result.payments,
        result.orders,
	failure_rate_threshold=failure_rate_threshold,
	failure_code_threshold=failure_code_threshold,
    )

    incident = analyze_incident(
        result.payments,
        result.orders,
	failure_rate_threshold=failure_rate_threshold,
	failure_code_threshold=failure_code_threshold,
    )

    recommendations = recommend_recoveries(
        result.payments,
        incident,
    )

    return {
    "simulation": {
        "seed": config.seed if config else 42,
        "merchant_count": (
            config.merchant_count
            if config
            else 20
        ),
        "customers_per_merchant": (
            config.customers_per_merchant
            if config
            else 100
        ),
        "orders_per_customer": (
            config.orders_per_customer
            if config
            else 5
        ),
    },
    "metrics": {
            "total_payments": metrics.total_payments,
            "successful_payments": metrics.successful_payments,
            "failed_payments": metrics.failed_payments,
            "total_volume": str(metrics.total_volume),
            "successful_volume": str(metrics.successful_volume),
            "failed_volume": str(metrics.failed_volume),
            "success_rate": metrics.success_rate,
            "failure_rate": metrics.failure_rate,
        },
        "success_rate_by_method": success_rate_by_method(
            result.payments
        ),
        "failure_code_distribution": failure_code_distribution(
            result.payments
        ),
        "failure_rate_by_merchant": {
            str(merchant_id): rate
            for merchant_id, rate in failure_rate_by_merchant(
                result.payments,
                result.orders,
            ).items()
        },
        "failure_rate_by_customer_segment": (
            failure_rate_by_customer_segment(
                result.payments,
                result.customers,
            )
        ),
        "anomalies": [
            {
                "metric": anomaly.metric,
                "dimension": anomaly.dimension,
                "value": anomaly.value,
                "baseline": anomaly.baseline,
                "threshold": anomaly.threshold,
                "severity": anomaly.severity,
            }
            for anomaly in anomalies
        ],
        "incident": {
            "detected": incident.detected,
            "severity": incident.severity,
            "affected_payments": incident.affected_payments,
            "affected_volume": str(incident.affected_volume),
            "affected_methods": incident.affected_methods,
            "affected_merchants": incident.affected_merchants,
            "dominant_failure_codes": incident.dominant_failure_codes,
            "recommended_strategy": (
                incident.recommended_strategy.value
            ),
        },
        "recovery_recommendations": [
            {
                "payment_id": recommendation.payment_id,
                "strategy": recommendation.strategy.value,
                "predicted_probability": (
                    recommendation.predicted_probability
                ),
                "predicted_revenue": str(
                    recommendation.predicted_revenue
                ),
                "reason": recommendation.reason,
            }
            for recommendation in recommendations
        ],
    }

@app.post("/recovery/run")
def run_recovery_api(
    config: SimulationRunConfig | None = None,
):
    result = run_simulation(config)

    return {
        "total_attempts": len(result.recovery_attempts),
        "succeeded": sum(
            1
            for attempt in result.recovery_attempts
            if attempt.status == RecoveryStatus.SUCCEEDED
        ),
        "failed": sum(
            1
            for attempt in result.recovery_attempts
            if attempt.status == RecoveryStatus.FAILED
        ),
        "predicted_revenue": str(
            sum(
                (
                    attempt.predicted_revenue
                    for attempt in result.recovery_attempts
                ),
                Decimal("0"),
            )
        ),
        "actual_revenue": str(
            sum(
                (
                    attempt.actual_revenue or Decimal("0")
                    for attempt in result.recovery_attempts
                ),
                Decimal("0"),
            )
        ),
        "attempts": [
            {
                "recovery_id": str(attempt.recovery_id),
                "payment_id": str(attempt.payment_id),
                "strategy": attempt.strategy.value,
                "predicted_probability": (
                    attempt.predicted_probability
                ),
                "predicted_revenue": str(
                    attempt.predicted_revenue
                ),
                "actual_revenue": str(
                    attempt.actual_revenue or Decimal("0")
                ),
                "status": attempt.status.value,
            }
            for attempt in result.recovery_attempts
        ],
    }

@app.post("/analytics/adaptive-recovery")
def adaptive_recovery_api(
    config: SimulationRunConfig | None = None,
    failure_rate_threshold: float = 0.10,
    failure_code_threshold: float = 0.40,
):
    result = run_simulation(config)

    incident = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=failure_rate_threshold,
        failure_code_threshold=failure_code_threshold,
    )

    decisions = rank_adaptive_recoveries(
        result.payments,
        incident,
    )

    total_predicted_revenue = sum(
        (
            decision.predicted_revenue
            for decision in decisions
        ),
        Decimal("0"),
    )

    high_priority = [
        decision
        for decision in decisions
        if decision.priority_score >= 70
    ]

    return {
        "summary": {
            "total_opportunities": len(decisions),
            "high_priority_opportunities": len(high_priority),
            "predicted_recoverable_revenue": str(
                total_predicted_revenue
            ),
            "incident_severity": incident.severity,
        },
        "opportunities": [
            decision_to_dict(decision)
            for decision in decisions
        ],
    }

@app.post("/analytics/counterfactual/{payment_id}")
def counterfactual_recovery_api(
    payment_id: UUID,
):
    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=20,
            customers_per_merchant=100,
            orders_per_customer=5,
        )
    )

    payment = next(
        (
            payment
            for payment in result.payments
            if payment.payment_id == payment_id
        ),
        None,
    )

    if payment is None:
        raise HTTPException(
            status_code=404,
            detail="Payment not found",
        )

    if payment.failure_code is None:
        raise HTTPException(
            status_code=400,
            detail="Counterfactual analysis requires a failed payment",
        )

    incident = analyze_incident(
        result.payments,
        result.orders,
        failure_rate_threshold=0.10,
        failure_code_threshold=0.40,
    )

    options = simulate_counterfactuals(
        payment,
        incident,
    )

    recommended = next(
        option
        for option in options
        if option.recommended
    )

    return {
        "payment": {
            "payment_id": str(payment.payment_id),
            "amount": str(payment.amount),
            "currency": payment.currency,
            "method": payment.method.value,
            "failure_code": payment.failure_code,
        },
        "recommendation": {
            "strategy": recommended.strategy.value,
            "probability": recommended.probability,
            "expected_revenue": str(
                recommended.expected_revenue
            ),
            "explanation": recommended.explanation,
        },
        "options": [
            {
                "strategy": option.strategy.value,
                "probability": option.probability,
                "expected_revenue": str(
                    option.expected_revenue
                ),
                "revenue_uplift": str(
                    option.revenue_uplift
                ),
                "relative_uplift": option.relative_uplift,
                "recommended": option.recommended,
                "explanation": option.explanation,
            }
            for option in options
        ],
    }