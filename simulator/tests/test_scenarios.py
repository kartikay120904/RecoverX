from random import Random

from simulator.config import PaymentSimulationConfig
from simulator.generators.customer import generate_customers
from simulator.generators.merchant import generate_merchants
from simulator.generators.order import generate_orders
from simulator.generators.payment import generate_payments
from simulator.config import PaymentSimulationConfig
from simulator.scenarios.incidents import (
    GatewayOutageScenario,
    UPIDegradationScenario,
)
from simulator.scenarios.normal import NormalScenario
from simulator.scenarios.registry import default_scenarios
from simulator.scenarios.resolver import ScenarioResolver


def test_gateway_outage_applies_during_outage_window():
    scenario = GatewayOutageScenario()

    assert scenario.applies_to(
        None,
        "card",
        14,
    )

    assert scenario.applies_to(
        None,
        "upi",
        15,
    )


def test_gateway_outage_does_not_apply_outside_window():
    scenario = GatewayOutageScenario()

    assert not scenario.applies_to(
        None,
        "card",
        13,
    )

    assert not scenario.applies_to(
        None,
        "card",
        16,
    )


def test_gateway_outage_has_low_success_rate():
    scenario = GatewayOutageScenario()

    assert scenario.payment_success_rate(
        None,
        "card",
        14,
    ) == 0.35


def test_upi_degradation_applies_only_to_upi():
    scenario = UPIDegradationScenario()

    assert scenario.applies_to(
        None,
        "upi",
        19,
    )

    assert not scenario.applies_to(
        None,
        "card",
        19,
    )


def test_normal_scenario_always_applies():
    config = PaymentSimulationConfig(seed=42)
    scenario = NormalScenario(config)

    assert scenario.applies_to(
        None,
        "card",
        10,
    )


def test_gateway_outage_has_priority_over_normal():
    config = PaymentSimulationConfig(seed=42)

    scenarios = default_scenarios(config)
    resolver = ScenarioResolver(scenarios)

    resolved = resolver.resolve(
        None,
        "card",
        14,
    )

    assert resolved.name == "gateway_outage"


def test_normal_is_used_when_no_incident_applies():
    config = PaymentSimulationConfig(seed=42)

    scenarios = default_scenarios(config)
    resolver = ScenarioResolver(scenarios)

    resolved = resolver.resolve(
        None,
        "card",
        10,
    )

    assert resolved.name == "normal"

def test_gateway_outage_increases_payment_failures():
    config = PaymentSimulationConfig(seed=42)
    rng = Random(42)

    merchants = generate_merchants(4)

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    customers = generate_customers(
        count=40,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    orders = generate_orders(
        count=1000,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    scenarios = default_scenarios(config)
    resolver = ScenarioResolver(scenarios)

    payments = generate_payments(
        orders=orders,
        rng=rng,
        config=config,
        scenario_resolver=resolver,
    )

    outage_payments = [
        payment
        for payment in payments
        if 14 <= payment.created_at.hour < 16
    ]

    failed_outage_payments = [
        payment
        for payment in outage_payments
        if payment.status.value == "failed"
    ]

    assert len(outage_payments) > 0

    outage_failure_rate = (
        len(failed_outage_payments)
        / len(outage_payments)
    )

    assert outage_failure_rate > 0.50