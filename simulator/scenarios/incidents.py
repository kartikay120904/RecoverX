from backend.app.domain.models import Order
from simulator.scenarios.base import SimulationScenario


class UPIDegradationScenario(SimulationScenario):
    name = "upi_degradation"

    def applies_to(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> bool:

        return (
            payment_method == "upi"
            and 19 <= timestamp_hour < 21
        )

    def payment_success_rate(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> float:

        return 0.72