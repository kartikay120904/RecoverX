from random import Random

from simulator.batch.payment_generator import (
    PaymentGenerator,
)

from simulator.batch.recovery_batch_factory import (
    RecoveryBatchFactory,
)

from simulator.batch.recovery_batch_runner import (
    RecoveryBatchResult,
    RecoveryBatchRunner,
)


class RecoverySimulationService:
    """
    High-level entry point for running a complete
    RecoverX batch simulation.

    Responsibilities:

    1. Create deterministic random state.
    2. Generate synthetic failed payments.
    3. Build the complete recovery workflow.
    4. Execute the recovery batch.
    5. Return the existing batch result.

    This service intentionally does not modify:

    - PaymentGenerator
    - RecoveryBatchFactory
    - RecoveryBatchRunner
    - RecoveryOrchestrator
    - RecoveryEscalationCoordinator
    - RecoveryEscalationAdapter
    - EscalationWorkflow
    """

    def __init__(
        self,
        payment_generator: PaymentGenerator | None = None,
        batch_runner: RecoveryBatchRunner | None = None,
    ) -> None:
        """
        Create a recovery simulation service.

        Dependencies can be injected for testing.
        """

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
    ) -> RecoveryBatchResult:
        """
        Run a complete deterministic recovery simulation.

        Args:
            count:
                Number of synthetic payments to generate.

            seed:
                Optional random seed.

        Returns:
            RecoveryBatchResult containing:

            - per-payment results
            - aggregated recovery metrics
        """

        if count < 0:
            raise ValueError(
                "count must be greater than or equal to zero."
            )

        rng = Random(
            seed
        )

        payments = (
            self.payment_generator.generate(
                count=count,
                rng=rng,
            )
        )

        return (
            self.batch_runner.run(
                payments=payments,
                rng=rng,
            )
        )