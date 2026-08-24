from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


def test_simulation_runner_generates_expected_counts():

    result = run_simulation(
        SimulationRunConfig(
            seed=42,
            merchant_count=2,
            customers_per_merchant=5,
            orders_per_customer=3,
        )
    )

    assert len(result.merchants) == 2
    assert len(result.customers) == 10
    assert len(result.orders) == 30
    assert len(result.payments) == 30


def test_simulation_is_deterministic():

    config = SimulationRunConfig(
        seed=42,
        merchant_count=2,
        customers_per_merchant=5,
        orders_per_customer=3,
    )

    first = run_simulation(config)
    second = run_simulation(config)

    assert [
        payment.model_dump()
        for payment in first.payments
    ] == [
        payment.model_dump()
        for payment in second.payments
    ]