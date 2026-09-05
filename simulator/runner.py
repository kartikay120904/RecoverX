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
    """
    Run the complete payment and recovery simulation.

    Workflow:

        Merchants
            ↓
        Customers
            ↓
        Orders
            ↓
        Payments
            ↓
        Payment lifecycle transitions
            ↓
        Failed payments
            ↓
        Recovery proposal
            ↓
        Recovery execution
            ↓
        Simulation report

    RecoveryExecutor is responsible for the recovery execution
    lifecycle. This runner must not attempt to mark an already
    executed recovery as succeeded or failed again.
    """

    # =========================================================
    # Configuration
    # =========================================================

    if run_config is None:
        run_config = SimulationRunConfig()

    rng = Random(
        run_config.seed
    )

    payment_config = PaymentSimulationConfig(
        seed=run_config.seed,
    )

    # =========================================================
    # Generate merchants
    # =========================================================

    merchants = generate_merchants(
        run_config.merchant_count,
    )

    merchant_ids = [
        merchant.merchant_id
        for merchant in merchants
    ]

    # =========================================================
    # Generate customers
    # =========================================================

    customer_count = (
        run_config.merchant_count
        * run_config.customers_per_merchant
    )

    customers = generate_customers(
        count=customer_count,
        merchant_ids=merchant_ids,
        rng=rng,
    )

    # =========================================================
    # Generate orders
    # =========================================================

    order_count = (
        len(customers)
        * run_config.orders_per_customer
    )

    orders = generate_orders(
        count=order_count,
        merchant_ids=merchant_ids,
        customers=customers,
        rng=rng,
    )

    # =========================================================
    # Configure scenarios
    # =========================================================

    scenarios = default_scenarios(
        payment_config,
        enable_upi_degradation=(
            run_config.enable_upi_degradation
        ),
        enable_gateway_outage=(
            run_config.enable_gateway_outage
        ),
    )

    scenario_resolver = ScenarioResolver(
        scenarios,
    )

    # =========================================================
    # Generate payments
    # =========================================================

    payments = generate_payments(
        orders=orders,
        rng=rng,
        config=payment_config,
        scenario_resolver=scenario_resolver,
    )

    # =========================================================
    # Payment lifecycle
    # =========================================================

    event_stream = EventStream()

    lifecycle = PaymentLifecycle(
        event_stream,
    )

    for payment in payments:

        # Preserve the generated outcome.
        intended_status = payment.status

        # Start every payment from CREATED so that
        # lifecycle transitions are explicitly recorded.
        payment.status = PaymentStatus.CREATED

        # -----------------------------------------------------
        # Successful payment
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Failed payment
        # -----------------------------------------------------

        elif intended_status == PaymentStatus.FAILED:

            lifecycle.transition(
                payment,
                PaymentStatus.FAILED,
                actor="payment_service",
                correlation_id=payment.payment_id,
            )

        # -----------------------------------------------------
        # Other statuses
        # -----------------------------------------------------

        else:
            payment.status = intended_status

    # =========================================================
    # Recovery services
    # =========================================================

    recovery_engine = RecoveryEngine()

    recovery_executor = RecoveryExecutor()

    recovery_attempts = []

    # =========================================================
    # Process failed payments
    # =========================================================

    for payment in payments:

        # Recovery is only applicable to failed payments.
        if payment.status != PaymentStatus.FAILED:
            continue

        # -----------------------------------------------------
        # Propose recovery
        # -----------------------------------------------------

        attempt = recovery_engine.propose(
            payment,
        )

        if attempt is None:
            continue

        # -----------------------------------------------------
        # Execute recovery
        # -----------------------------------------------------

        # IMPORTANT:
        #
        # RecoveryExecutor owns the execution lifecycle.
        #
        # Do NOT call:
        #
        #   mark_completed()
        #   mark_failed()
        #
        # here after execution.
        #
        # Doing so would attempt a duplicate transition such as:
        #
        # EXECUTING -> FAILED
        # followed by
        # FAILED -> FAILED
        #
        # which causes the lifecycle error:
        #
        # Expected EXECUTING, got FAILED.

        executed_attempt = recovery_executor.execute(
            attempt,
            payment,
            rng,
        )

        recovery_attempts.append(
            executed_attempt,
        )

    # =========================================================
    # Build analytics report
    # =========================================================

    report = build_simulation_report(
        payments=payments,
        orders=orders,
        customers=customers,
        merchants=merchants,
    )

    # =========================================================
    # Return simulation result
    # =========================================================

    return SimulationResult(
        merchants=merchants,
        customers=customers,
        orders=orders,
        payments=payments,
        events=event_stream.all(),
        recovery_attempts=recovery_attempts,
        report=report,
    )