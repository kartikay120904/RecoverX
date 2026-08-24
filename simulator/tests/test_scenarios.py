from decimal import Decimal
from uuid import uuid4

from backend.app.domain.models import Order
from simulator.scenarios.incidents import UPIDegradationScenario
from simulator.scenarios.normal import NormalScenario
from simulator.config import PaymentSimulationConfig


def create_order() -> Order:
    return Order(
        merchant_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("5000"),
    )


def test_normal_scenario_applies_everywhere():
    scenario = NormalScenario(
    PaymentSimulationConfig()
)
    order = create_order()

    assert scenario.applies_to(
        order,
        "upi",
        10,
    )

    assert scenario.applies_to(
        order,
        "card",
        20,
    )


def test_upi_incident_applies_only_to_upi():
    scenario = UPIDegradationScenario()
    order = create_order()

    assert scenario.applies_to(
        order,
        "upi",
        19,
    )

    assert scenario.applies_to(
        order,
        "upi",
        20,
    )

    assert not scenario.applies_to(
        order,
        "card",
        19,
    )


def test_upi_incident_does_not_apply_outside_window():
    scenario = UPIDegradationScenario()
    order = create_order()

    assert not scenario.applies_to(
        order,
        "upi",
        18,
    )

    assert not scenario.applies_to(
        order,
        "upi",
        21,
    )


def test_upi_incident_reduces_success_rate():
    scenario = UPIDegradationScenario()
    order = create_order()

    assert (
        scenario.payment_success_rate(
            order,
            "upi",
            19,
        )
        == 0.72
    )