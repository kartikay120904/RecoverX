from decimal import Decimal
from uuid import uuid4

from backend.app.domain.models import Order
from simulator.scenarios.incidents import UPIDegradationScenario
from simulator.scenarios.normal import NormalScenario
from simulator.scenarios.resolver import ScenarioResolver
from simulator.config import PaymentSimulationConfig



def create_order() -> Order:
    return Order(
        merchant_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("5000"),
    )


def test_resolver_returns_incident_scenario():
    resolver = ScenarioResolver(
        [
            NormalScenario(
                PaymentSimulationConfig()
            ),
            UPIDegradationScenario(),
        ]
    )

    scenario = resolver.resolve(
        create_order(),
        "upi",
        19,
    )

    assert scenario.name == "upi_degradation"


def test_resolver_returns_normal_scenario():
    resolver = ScenarioResolver(
        [
            NormalScenario(
                PaymentSimulationConfig()
            ),
            UPIDegradationScenario(),
        ]
    )

    scenario = resolver.resolve(
        create_order(),
        "card",
        19,
    )

    assert scenario.name == "normal"


def test_resolver_returns_normal_outside_incident_window():
    resolver = ScenarioResolver(
        [
            NormalScenario(
                PaymentSimulationConfig()
            ),
            UPIDegradationScenario(),
        ]
    )

    scenario = resolver.resolve(
        create_order(),
        "upi",
        15,
    )

    assert scenario.name == "normal"