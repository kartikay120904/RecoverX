from backend.app.domain.models import Order
from simulator.scenarios.base import SimulationScenario


class ScenarioResolver:
    def __init__(
        self,
        scenarios: list[SimulationScenario],
    ) -> None:
        self.scenarios = scenarios

    def resolve(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> SimulationScenario:

        for scenario in self.scenarios:
            if scenario.name == "normal":
                continue

            if scenario.applies_to(
                order,
                payment_method,
                timestamp_hour,
            ):
                return scenario

        for scenario in self.scenarios:
            if scenario.name == "normal":
                return scenario

        raise ValueError("No normal scenario configured.")