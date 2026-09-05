from __future__ import annotations

from dataclasses import dataclass
from random import Random

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
)

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
    RecoveryBatchRunner,
)


@dataclass(frozen=True)
class BatchSimulationConfig:
    """
    Configuration for a deterministic
    RecoverX batch simulation.
    """

    payment_count: int = 100

    seed: int = 42


class BatchSimulation:
    """
    High-level simulation entry point for RecoverX.

    Responsibilities:

    1. Generate deterministic payments.
    2. Run each payment through the complete
       recovery + escalation workflow.
    3. Aggregate measurable recovery metrics.

    This class does not modify or duplicate:

    - RecoveryOrchestrator
    - RecoveryEscalationCoordinator
    - EscalationWorkflow
    - RecoveryExecutor

    It only composes existing components.
    """

    def __init__(
        self,
        *,
        coordinator: RecoveryEscalationCoordinator,
        payment_generator: PaymentGenerator | None = None,
    ) -> None:

        self.coordinator = coordinator

        self.payment_generator = (
            payment_generator
            if payment_generator is not None
            else PaymentGenerator()
        )

        self.batch_runner = (
            RecoveryBatchRunner(
                coordinator=self.coordinator,
            )
        )

    def run(
        self,
        config: BatchSimulationConfig,
    ) -> RecoveryBatchResult:
        """
        Run a deterministic payment recovery batch.
        """

        if config.payment_count < 0:

            raise ValueError(
                "payment_count cannot be negative."
            )

        rng = Random(
            config.seed
        )

        payments = (
            self.payment_generator.generate(
                count=config.payment_count,
                rng=rng,
            )
        )

        return self.batch_runner.run(
            payments=payments,
            rng=rng,
        )