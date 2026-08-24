from random import Random

from simulator.config import PaymentSimulationConfig
from simulator.generators.customer import generate_customers
from simulator.generators.merchant import generate_merchants
from simulator.generators.order import generate_orders
from simulator.generators.payment import generate_payments
from simulator.scenarios.registry import default_scenarios
from simulator.scenarios.resolver import ScenarioResolver


def test_upi_degradation_scenario_reduces_success_rate():
    rng = Random(42)

    config = PaymentSimulationConfig(seed=42)

    merchants = generate_merchants(5)

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    customers = generate_customers(
        count=100,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    orders = generate_orders(
        count=500,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    scenarios = default_scenarios(config)
    resolver = ScenarioResolver(scenarios)

    upi_scenario = resolver.resolve(
        order=orders[0],
        payment_method="upi",
        timestamp_hour=20,
    )

    assert upi_scenario.name == "upi_degradation"

    assert (
        upi_scenario.payment_success_rate(
            order=orders[0],
            payment_method="upi",
            timestamp_hour=20,
        )
        == 0.72
    )


def test_normal_scenario_is_used_outside_incident_window():
    rng = Random(42)

    config = PaymentSimulationConfig(seed=42)

    merchants = generate_merchants(2)

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    customers = generate_customers(
        count=20,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    orders = generate_orders(
        count=50,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    resolver = ScenarioResolver(
        default_scenarios(config)
    )

    scenario = resolver.resolve(
        order=orders[0],
        payment_method="upi",
        timestamp_hour=12,
    )

    assert scenario.name == "normal"