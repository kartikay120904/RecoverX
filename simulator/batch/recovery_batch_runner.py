from dataclasses import dataclass
from random import Random
from typing import Iterable

from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
)

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
    RecoveryEscalationCoordinatorResult,
)

from simulator.batch.recovery_metrics import (
    RecoveryMetrics,
)


@dataclass(frozen=True)
class RecoveryBatchResult:
    """
    Complete result of processing a batch of payments.

    Contains:

    - per-payment recovery results
    - aggregated batch metrics
    """

    results: list[
        RecoveryEscalationCoordinatorResult
    ]

    metrics: RecoveryMetrics


class RecoveryBatchRunner:
    """
    Runs the RecoverX recovery and escalation workflow
    across a batch of payments.

    This class intentionally does not modify:

    - RecoveryOrchestrator
    - RecoveryEscalationAdapter
    - RecoveryEscalationCoordinator
    - EscalationWorkflow

    It acts only as a batch-level integration layer.
    """

    def __init__(
        self,
        coordinator: RecoveryEscalationCoordinator,
    ) -> None:

        self.coordinator = coordinator

    def run(
        self,
        *,
        payments: Iterable[Payment],
        rng: Random,
    ) -> RecoveryBatchResult:
        """
        Process all payments through the complete
        recovery and escalation workflow.
        """

        metrics = RecoveryMetrics()

        results: list[
            RecoveryEscalationCoordinatorResult
        ] = []

        for payment in payments:

            # -----------------------------------------
            # Step 1: Record processed payment
            # -----------------------------------------

            metrics.record_payment()

            # -----------------------------------------
            # Step 2: Execute complete workflow
            # -----------------------------------------

            result = (
                self.coordinator.recover(
                    payment=payment,
                    rng=rng,
                )
            )

            results.append(result)

            orchestration = (
                result.orchestration
            )

            attempt = (
                orchestration.attempt
            )

            # -----------------------------------------
            # Step 3: Payment flagged for recovery
            # -----------------------------------------

            if attempt is not None:

                metrics.record_flagged_payment()

                metrics.record_recovery_attempt()

            # -----------------------------------------
            # Step 4: Approval requirement
            # -----------------------------------------

            if (
                orchestration.requires_approval
            ):

                metrics.record_approval_required()

            # -----------------------------------------
            # Step 5: Recovery execution outcome
            # -----------------------------------------

            if orchestration.executed:

                if (
                    attempt is not None
                    and attempt.status
                    == RecoveryStatus.SUCCEEDED
                ):

                    metrics.record_success(
                        revenue=float(
                            attempt.actual_revenue
                            or 0
                        ),
                    )

                elif (
                    attempt is not None
                    and attempt.status
                    == RecoveryStatus.FAILED
                ):

                    metrics.record_failure()

            elif orchestration.blocked:

                metrics.record_blocked()

            # -----------------------------------------
            # Step 6: Escalation outcome
            # -----------------------------------------

            if (
                result.escalation is not None
                and result.escalation.escalation
                is not None
            ):

                metrics.record_escalation()

        return RecoveryBatchResult(
            results=results,
            metrics=metrics,
        )