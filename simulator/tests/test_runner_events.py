from collections import defaultdict

from simulator.runner import run_simulation
from simulator.simulation_config import SimulationRunConfig


def test_captured_payments_have_two_lifecycle_events():
    config = SimulationRunConfig(
        seed=42,
        merchant_count=2,
        customers_per_merchant=5,
        orders_per_customer=3,
    )

    result = run_simulation(config)

    events_by_payment = defaultdict(list)

    for event in result.events:
        events_by_payment[event.entity_id].append(event)

    for payment in result.payments:
        payment_events = events_by_payment[payment.payment_id]

        if payment.status.value == "captured":
            assert len(payment_events) == 2

            assert (
                payment_events[0].payload["new_status"]
                == "authorized"
            )

            assert (
                payment_events[1].payload["new_status"]
                == "captured"
            )


def test_failed_payments_have_one_lifecycle_event():
    config = SimulationRunConfig(
        seed=42,
        merchant_count=2,
        customers_per_merchant=5,
        orders_per_customer=3,
    )

    result = run_simulation(config)

    events_by_payment = defaultdict(list)

    for event in result.events:
        events_by_payment[event.entity_id].append(event)

    for payment in result.payments:
        payment_events = events_by_payment[payment.payment_id]

        if payment.status.value == "failed":
            assert len(payment_events) == 1

            assert (
                payment_events[0].payload["new_status"]
                == "failed"
            )


def test_payment_lifecycle_events_share_correlation_id():
    config = SimulationRunConfig(
        seed=42,
        merchant_count=2,
        customers_per_merchant=5,
        orders_per_customer=3,
    )

    result = run_simulation(config)

    events_by_payment = defaultdict(list)

    for event in result.events:
        events_by_payment[event.entity_id].append(event)

    for events in events_by_payment.values():
        correlation_ids = {
            event.correlation_id
            for event in events
        }

        assert len(correlation_ids) == 1