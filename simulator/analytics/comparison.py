from dataclasses import dataclass
from decimal import Decimal

from simulator.result import SimulationResult


@dataclass(frozen=True)
class SimulationComparison:
    baseline_failure_rate: float
    incident_failure_rate: float
    failure_rate_delta: float

    baseline_failed_payments: int
    incident_failed_payments: int
    failed_payments_delta: int

    baseline_failed_volume: Decimal
    incident_failed_volume: Decimal
    failed_volume_delta: Decimal


def compare_simulations(
    baseline: SimulationResult,
    incident: SimulationResult,
) -> SimulationComparison:

    baseline_report = baseline.report
    incident_report = incident.report

    if baseline_report is None:
        raise ValueError("Baseline simulation report is required.")

    if incident_report is None:
        raise ValueError("Incident simulation report is required.")

    baseline_metrics = baseline_report.payment_metrics
    incident_metrics = incident_report.payment_metrics
    
    return SimulationComparison(
        baseline_failure_rate=baseline_metrics.failure_rate,
        incident_failure_rate=incident_metrics.failure_rate,
        failure_rate_delta=(
            incident_metrics.failure_rate
            - baseline_metrics.failure_rate
        ),
        baseline_failed_payments=baseline_metrics.failed_payments,
        incident_failed_payments=incident_metrics.failed_payments,
        failed_payments_delta=(
            incident_metrics.failed_payments
            - baseline_metrics.failed_payments
        ),
        baseline_failed_volume=baseline_metrics.failed_volume,
        incident_failed_volume=incident_metrics.failed_volume,
        failed_volume_delta=(
            incident_metrics.failed_volume
            - baseline_metrics.failed_volume
        ),
    )