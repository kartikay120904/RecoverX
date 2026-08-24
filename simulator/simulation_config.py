from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationRunConfig:
    seed: int = 42
    merchant_count: int = 20
    customers_per_merchant: int = 100
    orders_per_customer: int = 5