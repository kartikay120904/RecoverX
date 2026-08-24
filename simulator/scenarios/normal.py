from backend.app.domain.models import Order
from simulator.config import PaymentSimulationConfig
from simulator.scenarios.base import SimulationScenario


class NormalScenario(SimulationScenario):
    name = "normal"

    def __init__(
        self,
        config: PaymentSimulationConfig,
    ) -> None:
        self.config = config

    def applies_to(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> bool:
        return True

    def payment_success_rate(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> float:

        return self.config.get_success_rates()[payment_method]