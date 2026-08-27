from decimal import Decimal

from pydantic import BaseModel

from backend.app.domain.enums import RecoveryStrategy


class HealthResponse(BaseModel):
    status: str
    service: str


class SimulationResponse(BaseModel):
    merchants: int
    customers: int
    orders: int
    payments: int
    events: int
    recovery_attempts: int


class MetricsResponse(BaseModel):
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_volume: Decimal
    successful_volume: Decimal
    failed_volume: Decimal
    success_rate: float
    failure_rate: float


class AnomalyResponse(BaseModel):
    metric: str
    dimension: str
    value: float
    baseline: float
    threshold: float
    severity: str


class IncidentResponse(BaseModel):
    detected: bool
    severity: str
    affected_payments: int
    affected_volume: Decimal
    affected_methods: list[str]
    affected_merchants: list[str]
    dominant_failure_codes: list[str]
    recommended_strategy: RecoveryStrategy


class RecoveryRecommendationResponse(BaseModel):
    payment_id: str
    strategy: RecoveryStrategy
    predicted_probability: float
    predicted_revenue: Decimal
    decision_score: float
    reason: str


class AnalyticsReportResponse(BaseModel):
    metrics: MetricsResponse
    success_rate_by_method: dict[str, float]
    failure_code_distribution: dict[str, int]
    failure_rate_by_merchant: dict[str, float]
    failure_rate_by_customer_segment: dict[str, float]
    anomalies: list[AnomalyResponse]
    incident: IncidentResponse
    recovery_recommendations: list[RecoveryRecommendationResponse]