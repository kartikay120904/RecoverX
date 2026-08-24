from datetime import datetime
from random import Random
from uuid import UUID, uuid5

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
)
from backend.app.domain.models import Order, Payment
from simulator.scenarios.resolver import ScenarioResolver
from simulator.config import PaymentSimulationConfig


FAILURE_CODES = [
    PaymentFailureCode.INSUFFICIENT_FUNDS,
    PaymentFailureCode.BANK_TIMEOUT,
    PaymentFailureCode.NETWORK_ERROR,
    PaymentFailureCode.PAYMENT_DECLINED,
    PaymentFailureCode.AUTHENTICATION_FAILED,
    PaymentFailureCode.GATEWAY_TIMEOUT,
]


def choose_payment_method(rng: Random) -> PaymentMethod:
    return rng.choices(
        population=list(PaymentMethod),
        weights=[45, 35, 12, 8],
        k=1,
    )[0]


def deterministic_payment_id(
    order_id: UUID,
    attempt_number: int,
) -> UUID:
    return uuid5(
        order_id,
        f"payment-attempt-{attempt_number}",
    )


def deterministic_timestamp(
    order: Order,
    attempt_number: int,
) -> datetime:
    return order.created_at.replace(
        microsecond=0
    )


def generate_payment_for_order(
    order: Order,
    rng: Random,
    config: PaymentSimulationConfig,
    attempt_number: int = 1,
    scenario_resolver: ScenarioResolver | None = None,
) -> Payment:

    method = choose_payment_method(rng)

    if scenario_resolver is None:
        success_rate = config.get_success_rates()[method.value]
    else:
        scenario = scenario_resolver.resolve(
            order=order,
            payment_method=method.value,
            timestamp_hour=order.created_at.hour,
        )

        success_rate = scenario.payment_success_rate(
            order=order,
            payment_method=method.value,
            timestamp_hour=order.created_at.hour,
        )

    succeeded = rng.random() < success_rate

    if succeeded:
        status = PaymentStatus.CAPTURED
        failure_code = None
    else:
        status = PaymentStatus.FAILED
        failure_code = rng.choice(FAILURE_CODES)

    timestamp = deterministic_timestamp(
        order,
        attempt_number,
    )

    return Payment(
        payment_id=deterministic_payment_id(
            order.order_id,
            attempt_number,
        ),
        order_id=order.order_id,
        customer_id=order.customer_id,
        amount=order.amount,
        currency=order.currency,
        method=method,
        status=status,
        failure_code=(
            failure_code.value
            if failure_code is not None
            else None
        ),
        attempt_number=attempt_number,
        created_at=timestamp,
        updated_at=timestamp,
    )


def generate_payments(
    orders: list[Order],
    rng: Random,
    config: PaymentSimulationConfig,
    scenario_resolver: ScenarioResolver | None = None,
) -> list[Payment]:

    if not orders:
        raise ValueError("At least one order is required.")

    return [
    generate_payment_for_order(
        order=order,
        rng=rng,
        config=config,
        scenario_resolver=scenario_resolver,
    )
    for order in orders
]