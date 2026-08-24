from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import Random
from uuid import UUID, uuid5

from backend.app.domain.enums import OrderStatus
from backend.app.domain.models import Order


ORDER_AMOUNTS_BY_SEGMENT = {
    "new": (200, 2500),
    "returning": (500, 5000),
    "high_value": (5000, 50000),
    "low_value": (100, 1200),
    "inactive": (300, 3000),
}
SIMULATION_NAMESPACE = UUID(
    "12345678-1234-5678-1234-567812345678"
)


SIMULATION_START = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)


def generate_orders(
    count: int,
    merchant_ids: list[UUID],
    customers: list,
    rng: Random,
) -> list[Order]:

    if count <= 0:
        raise ValueError("Order count must be greater than zero.")

    if not merchant_ids:
        raise ValueError("At least one merchant is required.")

    if not customers:
        raise ValueError("At least one customer is required.")

    orders: list[Order] = []

    for index in range(count):
        customer = rng.choice(customers)

        minimum, maximum = ORDER_AMOUNTS_BY_SEGMENT[
            customer.customer_segment
        ]

        amount = Decimal(
            str(
                rng.randint(
                    minimum,
                    maximum,
                )
            )
        )

        created_at = SIMULATION_START + timedelta(
            minutes=index,
        )

        orders.append(
            Order(
    order_id=uuid5(
        SIMULATION_NAMESPACE,
        f"order-{index}",
    ),
    merchant_id=customer.merchant_id,
                customer_id=customer.customer_id,
                amount=amount,
                currency="INR",
                status=OrderStatus.CREATED,
                created_at=created_at,
            )
        )

    return orders