from simulator.benchmark import run_benchmark


def test_benchmark_generates_at_least_10000_payments():
    result = run_benchmark(
        seed=42,
        merchant_count=100,
        customers_per_merchant=20,
        orders_per_customer=5,
    )

    assert result.merchants == 100
    assert result.customers == 2000
    assert result.orders == 10000
    assert result.payments == 10000
    assert result.events > 0


def test_benchmark_is_deterministic():
    first = run_benchmark(
        seed=42,
        merchant_count=10,
        customers_per_merchant=10,
        orders_per_customer=5,
    )

    second = run_benchmark(
        seed=42,
        merchant_count=10,
        customers_per_merchant=10,
        orders_per_customer=5,
    )

    assert first.merchants == second.merchants
    assert first.customers == second.customers
    assert first.orders == second.orders
    assert first.payments == second.payments
    assert first.events == second.events