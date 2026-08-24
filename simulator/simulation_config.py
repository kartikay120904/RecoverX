from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationRunConfig:
    seed: int = 42
    merchant_count: int = 20
    customers_per_merchant: int = 100
    orders_per_customer: int = 5

    enable_upi_degradation: bool = True
    enable_gateway_outage: bool = True

    def __post_init__(self) -> None:
        if self.merchant_count <= 0:
            raise ValueError("merchant_count must be greater than zero.")

        if self.customers_per_merchant <= 0:
            raise ValueError(
                "customers_per_merchant must be greater than zero."
            )

        if self.orders_per_customer <= 0:
            raise ValueError(
                "orders_per_customer must be greater than zero."
            )