from random import Random
from uuid import uuid4

import pytest

from simulator.generators.customer import generate_customers


def test_generate_customers():
    merchant_ids = [uuid4(), uuid4()]
    rng = Random(42)

    customers = generate_customers(
        count=100,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    assert len(customers) == 100

    assert all(
        customer.merchant_id in merchant_ids
        for customer in customers
    )

    assert all(
        len(customer.email_hash) == 64
        for customer in customers
    )


def test_customer_generation_is_deterministic():
    merchant_ids = [uuid4()]

    first = generate_customers(
        count=10,
        merchant_ids=merchant_ids,
        rng=Random(42),
    )

    second = generate_customers(
        count=10,
        merchant_ids=merchant_ids,
        rng=Random(42),
    )

    assert [
        customer.email_hash
        for customer in first
    ] == [
        customer.email_hash
        for customer in second
    ]


def test_customer_generation_requires_merchants():
    with pytest.raises(ValueError):
        generate_customers(
            count=10,
            merchant_ids=[],
            rng=Random(42),
        )