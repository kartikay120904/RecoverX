from dataclasses import dataclass

from backend.app.domain.enums import PaymentStatus
from backend.app.domain.models import Order, Payment


MIN_SAMPLE_SIZE = 20


@dataclass(frozen=True)
class Anomaly:
    metric: str
    dimension: str
    value: float
    baseline: float
    threshold: float
    severity: str


def _severity(value: float, threshold: float) -> str:
    if value >= threshold + 0.25:
        return "critical"

    if value >= threshold + 0.10:
        return "high"

    if value >= threshold:
        return "medium"

    return "normal"


def _failure_rate(payments: list[Payment]) -> float:
    if not payments:
        return 0.0

    failures = sum(
        payment.status == PaymentStatus.FAILED
        for payment in payments
    )

    return failures / len(payments)


def detect_overall_failure_rate_anomaly(
    payments: list[Payment],
    threshold: float = 0.20,
) -> Anomaly | None:
    if len(payments) < MIN_SAMPLE_SIZE:
        return None

    failure_rate = _failure_rate(payments)

    if failure_rate < threshold:
        return None

    return Anomaly(
        metric="failure_rate",
        dimension="overall",
        value=failure_rate,
        baseline=0.0,
        threshold=threshold,
        severity=_severity(failure_rate, threshold),
    )


def detect_method_anomalies(
    payments: list[Payment],
    threshold: float = 0.20,
) -> list[Anomaly]:
    grouped: dict[str, list[Payment]] = {}

    for payment in payments:
        method = payment.method.value
        grouped.setdefault(method, []).append(payment)

    anomalies: list[Anomaly] = []

    for method, method_payments in grouped.items():
        if len(method_payments) < MIN_SAMPLE_SIZE:
            continue

        failure_rate = _failure_rate(method_payments)

        if failure_rate < threshold:
            continue

        anomalies.append(
            Anomaly(
                metric="failure_rate",
                dimension=f"method:{method}",
                value=failure_rate,
                baseline=0.0,
                threshold=threshold,
                severity=_severity(failure_rate, threshold),
            )
        )

    return anomalies


def detect_merchant_anomalies(
    payments: list[Payment],
    orders: list[Order],
    threshold: float = 0.20,
) -> list[Anomaly]:
    order_to_merchant = {
        order.order_id: order.merchant_id
        for order in orders
    }

    grouped: dict[str, list[Payment]] = {}

    for payment in payments:
        merchant_id = order_to_merchant.get(payment.order_id)

        if merchant_id is None:
            continue

        key = str(merchant_id)
        grouped.setdefault(key, []).append(payment)

    anomalies: list[Anomaly] = []

    for merchant_id, merchant_payments in grouped.items():
        if len(merchant_payments) < MIN_SAMPLE_SIZE:
            continue

        failure_rate = _failure_rate(merchant_payments)

        if failure_rate < threshold:
            continue

        anomalies.append(
            Anomaly(
                metric="failure_rate",
                dimension=f"merchant:{merchant_id}",
                value=failure_rate,
                baseline=0.0,
                threshold=threshold,
                severity=_severity(failure_rate, threshold),
            )
        )

    return anomalies


def detect_failure_code_anomalies(
    payments: list[Payment],
    threshold: float = 0.40,
) -> list[Anomaly]:
    failed_payments = [
        payment
        for payment in payments
        if payment.status == PaymentStatus.FAILED
        and payment.failure_code is not None
    ]

    if len(failed_payments) < MIN_SAMPLE_SIZE:
        return []

    counts: dict[str, int] = {}

    for payment in failed_payments:
        assert payment.failure_code is not None

        counts[payment.failure_code] = (
            counts.get(payment.failure_code, 0) + 1
        )

    anomalies: list[Anomaly] = []

    total_failures = len(failed_payments)

    for failure_code, count in counts.items():
        concentration = count / total_failures

        if concentration < threshold:
            continue

        anomalies.append(
            Anomaly(
                metric="failure_code_concentration",
                dimension=f"failure_code:{failure_code}",
                value=concentration,
                baseline=0.0,
                threshold=threshold,
                severity=_severity(concentration, threshold),
            )
        )

    return anomalies


def detect_anomalies(
    payments: list[Payment],
    orders: list[Order],
    *,
    failure_rate_threshold: float = 0.20,
    failure_code_threshold: float = 0.40,
) -> list[Anomaly]:
    anomalies: list[Anomaly] = []

    overall = detect_overall_failure_rate_anomaly(
        payments,
        threshold=failure_rate_threshold,
    )

    if overall is not None:
        anomalies.append(overall)

    anomalies.extend(
        detect_method_anomalies(
            payments,
            threshold=failure_rate_threshold,
        )
    )

    anomalies.extend(
        detect_merchant_anomalies(
            payments,
            orders,
            threshold=failure_rate_threshold,
        )
    )

    anomalies.extend(
        detect_failure_code_anomalies(
            payments,
            threshold=failure_code_threshold,
        )
    )

    return anomalies