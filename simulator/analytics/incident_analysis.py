from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import PaymentStatus, RecoveryStrategy
from backend.app.domain.models import Order, Payment
from simulator.analytics.anomaly_detection import (
    Anomaly,
    detect_anomalies,
)


@dataclass(frozen=True)
class IncidentAnalysis:
    detected: bool
    severity: str
    affected_payments: int
    affected_volume: Decimal
    affected_methods: list[str]
    affected_merchants: list[str]
    dominant_failure_codes: list[str]
    recommended_strategy: RecoveryStrategy


def _severity_rank(severity: str) -> int:
    return {
        "normal": 0,
        "medium": 1,
        "high": 2,
        "critical": 3,
    }.get(severity, 0)


def _highest_severity(anomalies: list[Anomaly]) -> str:
    if not anomalies:
        return "normal"

    return max(
        anomalies,
        key=lambda anomaly: _severity_rank(anomaly.severity),
    ).severity


def _extract_methods(anomalies: list[Anomaly]) -> list[str]:
    return sorted(
        {
            anomaly.dimension.removeprefix("method:")
            for anomaly in anomalies
            if anomaly.dimension.startswith("method:")
        }
    )


def _extract_merchants(anomalies: list[Anomaly]) -> list[str]:
    return sorted(
        {
            anomaly.dimension.removeprefix("merchant:")
            for anomaly in anomalies
            if anomaly.dimension.startswith("merchant:")
        }
    )


def _extract_failure_codes(anomalies: list[Anomaly]) -> list[str]:
    return sorted(
        {
            anomaly.dimension.removeprefix("failure_code:")
            for anomaly in anomalies
            if anomaly.dimension.startswith("failure_code:")
        }
    )


def _recommend_strategy(
    severity: str,
) -> RecoveryStrategy:
    if severity == "critical":
        return RecoveryStrategy.ESCALATE

    if severity == "high":
        return RecoveryStrategy.RETRY_PAYMENT

    if severity == "medium":
        return RecoveryStrategy.SEND_REMINDER

    return RecoveryStrategy.NO_ACTION


def analyze_incident(
    payments: list[Payment],
    orders: list[Order],
    *,
    failure_rate_threshold: float = 0.20,
    failure_code_threshold: float = 0.40,
) -> IncidentAnalysis:
    anomalies = detect_anomalies(
        payments,
        orders,
        failure_rate_threshold=failure_rate_threshold,
        failure_code_threshold=failure_code_threshold,
    )

    if not anomalies:
        return IncidentAnalysis(
            detected=False,
            severity="normal",
            affected_payments=0,
            affected_volume=Decimal("0"),
            affected_methods=[],
            affected_merchants=[],
            dominant_failure_codes=[],
            recommended_strategy=RecoveryStrategy.NO_ACTION,
        )

    severity = _highest_severity(anomalies)

    failed_payments = [
        payment
        for payment in payments
        if payment.status == PaymentStatus.FAILED
    ]

    affected_volume = sum(
        (payment.amount for payment in failed_payments),
        Decimal("0"),
    )

    return IncidentAnalysis(
        detected=True,
        severity=severity,
        affected_payments=len(failed_payments),
        affected_volume=affected_volume,
        affected_methods=_extract_methods(anomalies),
        affected_merchants=_extract_merchants(anomalies),
        dominant_failure_codes=_extract_failure_codes(anomalies),
        recommended_strategy=_recommend_strategy(severity),
    )