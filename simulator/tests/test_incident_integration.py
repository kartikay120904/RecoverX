from simulator.analytics.anomaly_detection import detect_anomalies
from simulator.analytics.incident_analysis import analyze_incident
from simulator.config import PaymentSimulationConfig
from simulator.generators.customer import generate_customers
from simulator.generators.merchant import generate_merchants
from simulator.generators.order import generate_orders
from simulator.generators.payment import generate_payments
from simulator.scenarios.registry import default_scenarios
from simulator.scenarios.resolver import ScenarioResolver
from random import Random


def generate_incident_payments():
    rng = Random(42)

    config = PaymentSimulationConfig(seed=42)

    merchants = generate_merchants(5)

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    customers = generate_customers(
        count=100,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    orders = generate_orders(
        count=5000,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    resolver = ScenarioResolver(
        default_scenarios(config)
    )

    payments = generate_payments(
        orders=orders,
        rng=rng,
        config=config,
        scenario_resolver=resolver,
    )

    return payments, orders


def test_incident_scenarios_create_failures():
    payments, orders = generate_incident_payments()

    anomalies = detect_anomalies(
        payments,
        orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.40,
    )

    assert anomalies


def test_incident_analysis_detects_incident():
    payments, orders = generate_incident_payments()

    incident = analyze_incident(
        payments,
        orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.40,
    )

    assert incident.detected is True
    assert incident.severity in {
        "medium",
        "high",
        "critical",
    }
    assert incident.affected_payments > 0
    assert incident.affected_volume > 0