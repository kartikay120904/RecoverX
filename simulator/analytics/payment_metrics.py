from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal

from backend.app.domain.enums import PaymentStatus
from backend.app.domain.models import Customer, Merchant, Payment


@dataclass(frozen=True)
class PaymentMetrics:
    total_payments: int
    successful_payments: int
    failed_payments: int
    total_volume: Decimal
    successful_volume: Decimal
    failed_volume: Decimal

    @property
    def success_rate(self) -> float:
        if self.total_payments == 0:
            return 0.0

        return self.successful_payments / self.total_payments

    @property
    def failure_rate(self) -> float:
        if self.total_payments == 0:
            return 0.0

        return self.failed_payments / self.total_payments


def calculate_payment_metrics(
    payments: list[Payment],
) -> PaymentMetrics:
    successful = [
        payment
        for payment in payments
        if payment.status == PaymentStatus.CAPTURED
    ]

    failed = [
        payment
        for payment in payments
        if payment.status == PaymentStatus.FAILED
    ]

    total_volume = sum(
        (payment.amount for payment in payments),
        Decimal("0"),
    )

    successful_volume = sum(
        (payment.amount for payment in successful),
        Decimal("0"),
    )

    failed_volume = sum(
        (payment.amount for payment in failed),
        Decimal("0"),
    )

    return PaymentMetrics(
        total_payments=len(payments),
        successful_payments=len(successful),
        failed_payments=len(failed),
        total_volume=total_volume,
        successful_volume=successful_volume,
        failed_volume=failed_volume,
    )


def success_rate_by_method(
    payments: list[Payment],
) -> dict[str, float]:
    totals: Counter[str] = Counter()
    successes: Counter[str] = Counter()

    for payment in payments:
        method = payment.method.value

        totals[method] += 1

        if payment.status == PaymentStatus.CAPTURED:
            successes[method] += 1

    return {
        method: successes[method] / count
        for method, count in totals.items()
    }


def failure_code_distribution(
    payments: list[Payment],
) -> dict[str, int]:
    failures = Counter(
        payment.failure_code
        for payment in payments
        if payment.status == PaymentStatus.FAILED
        and payment.failure_code is not None
    )

    return dict(failures)


def failure_rate_by_merchant(
    payments: list[Payment],
    orders: list,
) -> dict:
    order_to_merchant = {
        order.order_id: order.merchant_id
        for order in orders
    }

    totals: Counter = Counter()
    failures: Counter = Counter()

    for payment in payments:
        merchant_id = order_to_merchant[payment.order_id]

        totals[merchant_id] += 1

        if payment.status == PaymentStatus.FAILED:
            failures[merchant_id] += 1

    return {
        merchant_id: failures[merchant_id] / count
        for merchant_id, count in totals.items()
    }


def failure_rate_by_customer_segment(
    payments: list[Payment],
    customers: list[Customer],
) -> dict[str, float]:
    customer_to_segment = {
        customer.customer_id: customer.customer_segment
        for customer in customers
    }

    totals: Counter[str] = Counter()
    failures: Counter[str] = Counter()

    for payment in payments:
        segment = customer_to_segment[payment.customer_id]

        totals[segment] += 1

        if payment.status == PaymentStatus.FAILED:
            failures[segment] += 1

    return {
        segment: failures[segment] / count
        for segment, count in totals.items()
    }