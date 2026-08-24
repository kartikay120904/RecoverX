from dataclasses import dataclass
from time import perf_counter

from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


@dataclass(frozen=True)
class BenchmarkResult:
    merchants: int
    customers: int
    orders: int
    payments: int
    events: int
    elapsed_seconds: float

    @property
    def payments_per_second(self) -> float:
        if self.elapsed_seconds <= 0:
            return 0.0

        return self.payments / self.elapsed_seconds


def run_benchmark(
    *,
    seed: int = 42,
    merchant_count: int = 100,
    customers_per_merchant: int = 20,
    orders_per_customer: int = 5,
) -> BenchmarkResult:
    config = SimulationRunConfig(
        seed=seed,
        merchant_count=merchant_count,
        customers_per_merchant=customers_per_merchant,
        orders_per_customer=orders_per_customer,
    )

    started = perf_counter()

    result = run_simulation(config)

    elapsed = perf_counter() - started

    return BenchmarkResult(
        merchants=len(result.merchants),
        customers=len(result.customers),
        orders=len(result.orders),
        payments=len(result.payments),
        events=len(result.events),
        elapsed_seconds=elapsed,
    )