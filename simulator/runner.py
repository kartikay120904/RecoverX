from random import Random

from backend.app.domain.enums import PaymentStatus
from simulator.analytics.report import build_simulation_report
from simulator.config import PaymentSimulationConfig
from simulator.event_stream import EventStream
from simulator.generators.customer import generate_customers
from simulator.generators.merchant import generate_merchants
from simulator.generators.order import generate_orders
from simulator.generators.payment import generate_payments
from simulator.payment_lifecycle import PaymentLifecycle
from simulator.recovery.engine import RecoveryEngine
from simulator.recovery.executor import RecoveryExecutor
from simulator.result import SimulationResult
from simulator.scenarios.registry import default_scenarios
from simulator.scenarios.resolver import ScenarioResolver
from simulator.simulation_config import SimulationRunConfig


def run_simulation(
    run_config: SimulationRunConfig | None = None,
) -> SimulationResult:
    if run_config is None:
        run_config = SimulationRunConfig()

    rng = Random(run_config.seed)

    payment_config = PaymentSimulationConfig(
        seed=run_config.seed,
    )

    merchants = generate_merchants(
        run_config.merchant_count,
    )

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    customers = generate_customers(
        count=(
            run_config.merchant_count
            * run_config.customers_per_merchant
        ),
        merchant_ids=merchant_ids,
        rng=rng,
    )

    orders = generate_orders(
        count=(
            len(customers)
            * run_config.orders_per_customer
        ),
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    scenarios = default_scenarios(
        payment_config,
        enable_upi_degradation=run_config.enable_upi_degradation,
        enable_gateway_outage=run_config.enable_gateway_outage,
    )

    scenario_resolver = ScenarioResolver(
        scenarios,
    )

    payments = generate_payments(
        orders=orders,
        rng=rng,
        config=payment_config,
        scenario_resolver=scenario_resolver,
    )

    event_stream = EventStream()
    lifecycle = PaymentLifecycle(event_stream)

    for payment in payments:
        intended_status = payment.status

        payment.status = PaymentStatus.CREATED

        if intended_status == PaymentStatus.CAPTURED:
            lifecycle.transition(
                payment,
                PaymentStatus.AUTHORIZED,
                actor="payment_service",
                correlation_id=payment.payment_id,
            )

            lifecycle.transition(
                payment,
                PaymentStatus.CAPTURED,
                actor="payment_service",
                correlation_id=payment.payment_id,
            )

        elif intended_status == PaymentStatus.FAILED:
            lifecycle.transition(
                payment,
                PaymentStatus.FAILED,
                actor="payment_service",
                correlation_id=payment.payment_id,
            )
        recovery_engine = RecoveryEngine()
    recovery_executor = RecoveryExecutor()

    recovery_attempts = []

    for payment in payments:
        if payment.status != PaymentStatus.FAILED:
            continue

        attempt = recovery_engine.propose(payment)

        if attempt is None:
            continue

        executed_attempt = recovery_executor.execute(
            attempt,
            payment,
            rng,
        )

        recovery_attempts.append(executed_attempt)

    report = build_simulation_report(
        payments=payments,
        orders=orders,
        customers=customers,
        merchants=merchants,
)

    return SimulationResult(
        merchants=merchants,
        customers=customers,
        orders=orders,
        payments=payments,
        events=event_stream.all(),
        recovery_attempts=recovery_attempts,
        report=report,
)