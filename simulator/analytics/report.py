from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import Customer, Merchant, Order, Payment
from simulator.analytics.anomaly_detection import (
    Anomaly,
    detect_anomalies,
)
from simulator.analytics.incident_analysis import IncidentAnalysis, analyze_incident
from simulator.analytics.payment_metrics import (
    PaymentMetrics,
    calculate_payment_metrics,
    failure_code_distribution,
    failure_rate_by_customer_segment,
    failure_rate_by_merchant,
    success_rate_by_method,
)
from simulator.analytics.recovery_recommendation import (
    RecoveryRecommendation,
    recommend_recoveries,
)


@dataclass(frozen=True)
class SimulationReport:
    payment_metrics: PaymentMetrics
    success_rate_by_method: dict[str, float]
    failure_code_distribution: dict[str, int]
    failure_rate_by_merchant: dict
    failure_rate_by_customer_segment: dict[str, float]

    anomalies: list[Anomaly]
    incident: IncidentAnalysis

    recovery_recommendations: list[RecoveryRecommendation]

    total_recovery_recommendations: int
    predicted_recovery_revenue: Decimal


def build_simulation_report(
    payments: list[Payment],
    orders: list[Order],
    customers: list[Customer],
    merchants: list[Merchant],
) -> SimulationReport:
    payment_metrics = calculate_payment_metrics(payments)

    method_rates = success_rate_by_method(payments)

    failure_codes = failure_code_distribution(payments)

    merchant_rates = failure_rate_by_merchant(
        payments,
        orders,
    )

    customer_segment_rates = failure_rate_by_customer_segment(
        payments,
        customers,
    )

    anomalies = detect_anomalies(
        payments,
        orders,
    )
    incident = analyze_incident(
        payments,
        orders,
    )

    recommendations = recommend_recoveries(
        payments,
        incident,
    )

    predicted_recovery_revenue = sum(
        (
            recommendation.predicted_revenue
            for recommendation in recommendations
        ),
        Decimal("0"),
    )

    return SimulationReport(
        payment_metrics=payment_metrics,
        success_rate_by_method=method_rates,
        failure_code_distribution=failure_codes,
        failure_rate_by_merchant=merchant_rates,
        failure_rate_by_customer_segment=customer_segment_rates,
        anomalies=anomalies,
        incident=incident,
        recovery_recommendations=recommendations,
        total_recovery_recommendations=len(recommendations),
        predicted_recovery_revenue=predicted_recovery_revenue,
    )