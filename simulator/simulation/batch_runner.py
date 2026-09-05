from dataclasses import dataclass
from random import Random

from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.recovery.executor import (
    RecoveryExecutor,
)
from simulator.recovery.orchestrator import (
    RecoveryOrchestrator,
)


@dataclass(frozen=True)
class BatchRecoveryResult:
    """
    Immutable result of processing a batch of
    payments through the recovery workflow.
    """

    payments: tuple[Payment, ...]
    attempts: tuple[RecoveryAttempt, ...]

    total_payments: int
    proposals_created: int
    executions_completed: int
    successful_recoveries: int
    failed_recoveries: int
    escalations_created: int


class BatchRecoveryRunner:
    """
    Executes an end-to-end batch recovery workflow.

    Workflow:

        Payment
            ↓
        RecoveryOrchestrator.propose()
            ↓
        approve()
            ↓
        schedule()
            ↓
        RecoveryExecutor.execute()
            ↓
        record_terminal_result()
            ↓
        escalation evaluation

    Existing recovery components are composed
    without modifying their implementation.
    """

    def __init__(
        self,
        *,
        orchestrator: (
            RecoveryOrchestrator | None
        ) = None,
        executor: (
            RecoveryExecutor | None
        ) = None,
    ) -> None:

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else RecoveryOrchestrator()
        )

        self.executor = (
            executor
            if executor is not None
            else RecoveryExecutor()
        )

    def run(
        self,
        *,
        payments: list[Payment],
        rng: Random,
    ) -> BatchRecoveryResult:
        """
        Process a batch of payments through the
        complete recovery workflow.
        """

        attempts: list[
            RecoveryAttempt
        ] = []

        successful_recoveries = 0
        failed_recoveries = 0
        escalations_created = 0

        for payment in payments:

            attempt = (
                self.orchestrator.propose(
                    payment
                )
            )

            # No safe automated recovery action.
            if attempt is None:

                escalation = (
                    self.orchestrator.evaluate_escalation(
                        payment=payment,
                        attempt=None,
                        has_recovery_action=False,
                    )
                )

                if escalation is not None:
                    escalations_created += 1

                continue

            attempts.append(
                attempt
            )

            # ---------------------------------
            # Approval
            # ---------------------------------

            self.orchestrator.approve(
                attempt
            )

            # ---------------------------------
            # Scheduling
            # ---------------------------------

            self.orchestrator.schedule(
                attempt
            )

            # ---------------------------------
            # Execution
            #
            # RecoveryExecutor owns the
            # transition to EXECUTING and the
            # terminal outcome.
            # ---------------------------------

            result = (
                self.executor.execute(
                    attempt=attempt,
                    payment=payment,
                    rng=rng,
                )
            )

            # ---------------------------------
            # Record terminal outcome
            # ---------------------------------

            self.orchestrator.record_terminal_result(
                result,
                payment=payment,
            )

            # ---------------------------------
            # Escalation
            # ---------------------------------

            escalation = (
                self.orchestrator.evaluate_escalation(
                    payment=payment,
                    attempt=result,
                )
            )

            if escalation is not None:
                escalations_created += 1

            # ---------------------------------
            # Metrics
            # ---------------------------------

            if (
                result.status
                == RecoveryStatus.SUCCEEDED
            ):
                successful_recoveries += 1

            elif (
                result.status
                == RecoveryStatus.FAILED
            ):
                failed_recoveries += 1

        executions_completed = (
            successful_recoveries
            + failed_recoveries
        )

        return BatchRecoveryResult(
            payments=tuple(payments),
            attempts=tuple(attempts),
            total_payments=len(
                payments
            ),
            proposals_created=len(
                attempts
            ),
            executions_completed=(
                executions_completed
            ),
            successful_recoveries=(
                successful_recoveries
            ),
            failed_recoveries=(
                failed_recoveries
            ),
            escalations_created=(
                escalations_created
            ),
        )