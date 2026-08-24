from simulator.config import PaymentSimulationConfig
from simulator.scenarios.base import SimulationScenario
from simulator.scenarios.incidents import (
    GatewayOutageScenario,
    UPIDegradationScenario,
)
from simulator.scenarios.normal import NormalScenario


def default_scenarios(
    config: PaymentSimulationConfig,
    *,
    enable_upi_degradation: bool = True,
    enable_gateway_outage: bool = True,
) -> list[SimulationScenario]:

    scenarios: list[SimulationScenario] = [
        NormalScenario(config),
    ]

    if enable_upi_degradation:
        scenarios.append(UPIDegradationScenario())

    if enable_gateway_outage:
        scenarios.append(GatewayOutageScenario())

    return scenarios