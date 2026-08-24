from simulator.config import PaymentSimulationConfig
from simulator.scenarios.base import SimulationScenario
from simulator.scenarios.incidents import UPIDegradationScenario
from simulator.scenarios.normal import NormalScenario


def default_scenarios(
    config: PaymentSimulationConfig,
) -> list[SimulationScenario]:

    return [
        NormalScenario(config),
        UPIDegradationScenario(),
    ]
