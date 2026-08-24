from random import Random

from simulator.analytics.incident_analysis import analyze_incident
from simulator.analytics.recovery_recommendation import recommend_recoveries
from simulator.config import PaymentSimulationConfig
from simulator.generators.customer import generate_customers
from simulator.generators.merchant import generate_merchants
from simulator.generators.order import generate_orders
from simulator.generators.payment import generate_payments
from simulator.scenarios.registry import default_scenarios
from simulator.scenarios.resolver import ScenarioResolver


def generate_incident_data():
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


def test_incident_generates_recovery_recommendations():
    payments, orders = generate_incident_data()

    incident = analyze_incident(
        payments,
        orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.40,
    )

    recommendations = recommend_recoveries(
        payments,
        incident,
    )

    assert incident.detected is True
    assert len(recommendations) > 0


def test_recommendations_contain_valid_strategies():
    payments, orders = generate_incident_data()

    incident = analyze_incident(
        payments,
        orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.40,
    )

    recommendations = recommend_recoveries(
        payments,
        incident,
    )

    valid_strategies = {
        "retry_payment",
        "send_reminder",
        "recovery_link",
        "incentive",
        "escalate",
        "no_action",
    }

    assert all(
        recommendation.strategy.value
        in valid_strategies
        for recommendation in recommendations
    )


def test_recommendations_have_predicted_revenue():
    payments, orders = generate_incident_data()

    incident = analyze_incident(
        payments,
        orders,
        failure_rate_threshold=0.05,
        failure_code_threshold=0.40,
    )

    recommendations = recommend_recoveries(
        payments,
        incident,
    )

    assert all(
        recommendation.predicted_revenue >= 0
        for recommendation in recommendations
    )