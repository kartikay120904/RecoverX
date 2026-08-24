from random import Random
from uuid import uuid4

import pytest

from simulator.generators.customer import generate_customers
from simulator.generators.order import generate_orders
from backend.app.domain.enums import OrderStatus


def test_generate_orders():
    merchant_ids = [uuid4(), uuid4()]

    customers = generate_customers(
        count=100,
        merchant_ids=merchant_ids,
        rng=Random(42),
    )

    orders = generate_orders(
        count=200,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=Random(42),
    )

    assert len(orders) == 200

    assert all(
        order.amount > 0
        for order in orders
    )

    assert all(
        order.merchant_id in merchant_ids
        for order in orders
    )

    assert all(
    order.status == OrderStatus.CREATED
    for order in orders
)


def test_orders_reference_existing_customers():
    merchant_ids = [uuid4()]

    customers = generate_customers(
        count=50,
        merchant_ids=merchant_ids,
        rng=Random(42),
    )

    customer_ids = {
        customer.customer_id
        for customer in customers
    }

    orders = generate_orders(
        count=100,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=Random(42),
    )

    assert all(
        order.customer_id in customer_ids
        for order in orders
    )


def test_order_generation_is_deterministic():
    merchant_ids = [uuid4()]

    customers = generate_customers(
        count=50,
        merchant_ids=merchant_ids,
        rng=Random(42),
    )

    first = generate_orders(
        count=50,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=Random(99),
    )

    second = generate_orders(
        count=50,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=Random(99),
    )

    assert [
        order.amount
        for order in first
    ] == [
        order.amount
        for order in second
    ]


def test_order_generation_requires_customers():
    with pytest.raises(ValueError):
        generate_orders(
            count=10,
            merchant_ids=[uuid4()],
            customers=[],
            rng=Random(42),
        )