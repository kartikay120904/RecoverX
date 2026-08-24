from random import Random
from uuid import uuid4

import pytest

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
)
from simulator.scenarios.incidents import UPIDegradationScenario
from simulator.scenarios.normal import NormalScenario
from simulator.scenarios.resolver import ScenarioResolver
from backend.app.domain.models import Customer, Order
from simulator.config import PaymentSimulationConfig
from simulator.generators.payment import (
    generate_payment_for_order,
    generate_payments,
)


def create_order() -> Order:
    return Order(
        merchant_id=uuid4(),
        customer_id=uuid4(),
        amount=2500,
        currency="INR",
    )

def test_scenario_resolver_changes_payment_success_rate():
    order = create_order()

    resolver = ScenarioResolver(
        [
            NormalScenario(
                PaymentSimulationConfig()
            ),
            UPIDegradationScenario(),
        ]
    )

    normal = resolver.resolve(
        order=order,
        payment_method="upi",
        timestamp_hour=15,
    )

    incident = resolver.resolve(
        order=order,
        payment_method="upi",
        timestamp_hour=19,
    )

    assert normal.name == "normal"
    assert incident.name == "upi_degradation"

    assert (
        normal.payment_success_rate(
            order,
            "upi",
            15,
        )
        == 0.92
    )

    assert (
        incident.payment_success_rate(
            order,
            "upi",
            19,
        )
        == 0.72
    )
    
def test_generate_payment():
    order = create_order()

    payment = generate_payment_for_order(
        order=order,
        rng=Random(42),
        config=PaymentSimulationConfig(),
    )

    assert payment.order_id == order.order_id
    assert payment.customer_id == order.customer_id
    assert payment.amount == order.amount
    assert payment.currency == "INR"
    assert payment.attempt_number == 1
    assert payment.method in list(PaymentMethod)


def test_successful_payment_has_no_failure_code():
    order = create_order()

    config = PaymentSimulationConfig(
        success_rates={
            "upi": 1.0,
            "card": 1.0,
            "netbanking": 1.0,
            "wallet": 1.0,
        }
    )

    payment = generate_payment_for_order(
        order=order,
        rng=Random(42),
        config=config,
    )

    assert payment.status == PaymentStatus.CAPTURED
    assert payment.failure_code is None


def test_failed_payment_has_failure_code():
    order = create_order()

    config = PaymentSimulationConfig(
        success_rates={
            "upi": 0.0,
            "card": 0.0,
            "netbanking": 0.0,
            "wallet": 0.0,
        }
    )

    payment = generate_payment_for_order(
        order=order,
        rng=Random(42),
        config=config,
    )

    assert payment.status == PaymentStatus.FAILED
    assert payment.failure_code in [
        code.value
        for code in PaymentFailureCode
    ]


def test_payment_generation_is_deterministic():
    order = create_order()

    config = PaymentSimulationConfig()

    first = generate_payment_for_order(
        order=order,
        rng=Random(42),
        config=config,
    )

    second = generate_payment_for_order(
        order=order,
        rng=Random(42),
        config=config,
    )

    assert first.model_dump() == second.model_dump()


def test_generate_payments_requires_orders():
    with pytest.raises(ValueError):
        generate_payments(
            orders=[],
            rng=Random(42),
            config=PaymentSimulationConfig(),
        )