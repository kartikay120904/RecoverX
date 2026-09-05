from dataclasses import dataclass
from random import Random

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.recovery_batch_factory import (
    RecoveryBatchFactory,
)
from simulator.batch.recovery_simulation_config import (
    RecoverySimulationConfig,
)
from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
    RecoveryBatchRunner,
)


@dataclass(frozen=True)
class RecoveryBatchSimulationResult:
    """
    Complete result of a RecoverX batch simulation.

    Contains:

    - generated payments
    - batch recovery results
    """

    payments: list

    batch_result: RecoveryBatchResult


class RecoveryBatchSimulation:
    """
    High-level deterministic batch simulation.

    Responsibilities:

    1. Generate payments.
    2. Execute batch recovery.
    3. Return the complete simulation result.

    This class does not modify existing recovery,
    escalation, orchestration, or execution logic.
    """

    def __init__(
        self,
        *,
        payment_generator: PaymentGenerator | None = None,
        batch_runner: RecoveryBatchRunner | None = None,
    ) -> None:

        self.payment_generator = (
            payment_generator
            if payment_generator is not None
            else PaymentGenerator()
        )

        self.batch_runner = (
            batch_runner
            if batch_runner is not None
            else RecoveryBatchFactory.create()
        )

    def run(
        self,
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoveryBatchSimulationResult:
        """
        Run a deterministic batch simulation.

        Args:
            count:
                Number of payments to simulate.

            seed:
                Random seed used for deterministic
                payment generation and recovery.

        Returns:
            Complete simulation result.

        Raises:
            ValueError:
                If count is negative.
        """

        if count < 0:
            raise ValueError(
                "Simulation count cannot be negative."
            )

        rng = Random(seed)

        payments = (
            self.payment_generator.generate(
                count=count,
                rng=rng,
            )
        )

        batch_result = (
            self.batch_runner.run(
                payments=payments,
                rng=rng,
            )
        )

        return RecoveryBatchSimulationResult(
            payments=payments,
            batch_result=batch_result,
        )

    def run_config(
        self,
        *,
        config: RecoverySimulationConfig,
    ) -> RecoveryBatchSimulationResult:
        """
        Run a simulation using an immutable
        simulation configuration.

        This method delegates to the existing run()
        method to preserve existing behavior.
        """

        return self.run(
            count=config.count,
            seed=config.seed,
        )