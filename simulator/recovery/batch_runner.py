from dataclasses import dataclass
from decimal import Decimal
from random import Random

from backend.app.domain.enums import RecoveryStatus
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
    Immutable result of executing a recovery batch.
    """

    total_payments: int
    total_failed_payments: int
    total_recovery_proposals: int
    total_recovered: int
    total_failed_recoveries: int
    total_unrecoverable: int

    total_revenue_at_risk: Decimal
    total_recovered_revenue: Decimal

    recovery_rate: float

    attempts: tuple[
        RecoveryAttempt,
        ...
    ]


class BatchRecoveryRunner:
    """
    Executes an end-to-end recovery workflow
    across a batch of payments.

    Workflow:

        Payment
            ↓
        Recovery Proposal
            ↓
        Approval
            ↓
        Scheduling
            ↓
        Execution
            ↓
        Terminal Result
            ↓
        Batch Metrics
    """

    def __init__(
        self,
        orchestrator: (
            RecoveryOrchestrator | None
        ) = None,
        executor: (
            RecoveryExecutor | None
        ) = None,
        rng: (
            Random | None
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

        self.rng = (
            rng
            if rng is not None
            else Random(42)
        )

    def run(
        self,
        payments: list[Payment],
    ) -> BatchRecoveryResult:
        """
        Execute recovery across a batch of payments.
        """

        attempts: list[
            RecoveryAttempt
        ] = []

        total_failed_payments = 0

        total_recovery_proposals = 0

        total_recovered = 0

        total_failed_recoveries = 0

        total_unrecoverable = 0

        total_revenue_at_risk = Decimal(
            "0"
        )

        total_recovered_revenue = Decimal(
            "0"
        )

        for payment in payments:

            # ---------------------------------
            # Track failed payment metrics
            # ---------------------------------

            if (
                payment.status.value
                == "failed"
            ):

                total_failed_payments += 1

                total_revenue_at_risk += (
                    payment.amount
                )

            # ---------------------------------
            # Create recovery proposal
            # ---------------------------------

            attempt = (
                self.orchestrator.propose(
                    payment
                )
            )

            # ---------------------------------
            # No recovery action available
            # ---------------------------------

            if attempt is None:

                total_unrecoverable += 1

                continue

            total_recovery_proposals += 1

            # ---------------------------------
            # Approve proposal
            # ---------------------------------

            self.orchestrator.approve(
                attempt
            )

            # ---------------------------------
            # Schedule recovery
            # ---------------------------------

            self.orchestrator.schedule(
                attempt
            )

            # ---------------------------------
            # Execute recovery
            # ---------------------------------

            execution_result = (
                self.executor.execute(
                    attempt=attempt,
                    payment=payment,
                    rng=self.rng,
                )
            )

            # ---------------------------------
            # Resolve execution result
            #
            # The executor may either:
            #
            # 1. Return a RecoveryAttempt
            # 2. Mutate the attempt in place
            #    and return None
            # ---------------------------------

            if isinstance(
                execution_result,
                RecoveryAttempt,
            ):

                result = execution_result

            else:

                result = attempt

            # ---------------------------------
            # Ensure terminal recovery result
            # ---------------------------------

            if (
                result.status
                not in {
                    RecoveryStatus.SUCCEEDED,
                    RecoveryStatus.FAILED,
                }
            ):

                raise RuntimeError(
                    "Recovery execution did not "
                    "produce a terminal status. "
                    f"Got {result.status}."
                )

            # ---------------------------------
            # Record terminal result
            # ---------------------------------

            self.orchestrator.record_terminal_result(
                result,
                payment=payment,
            )

            attempts.append(
                result
            )

            # ---------------------------------
            # Aggregate metrics
            # ---------------------------------

            if (
                result.status
                == RecoveryStatus.SUCCEEDED
            ):

                total_recovered += 1

                total_recovered_revenue += (
                    result.actual_revenue
                    or Decimal("0")
                )

            elif (
                result.status
                == RecoveryStatus.FAILED
            ):

                total_failed_recoveries += 1

        # ---------------------------------
        # Calculate recovery rate
        # ---------------------------------

        recovery_rate = (
            total_recovered
            / total_recovery_proposals
            if total_recovery_proposals > 0
            else 0.0
        )

        # ---------------------------------
        # Return batch result
        # ---------------------------------

        return BatchRecoveryResult(
            total_payments=len(
                payments
            ),
            total_failed_payments=(
                total_failed_payments
            ),
            total_recovery_proposals=(
                total_recovery_proposals
            ),
            total_recovered=(
                total_recovered
            ),
            total_failed_recoveries=(
                total_failed_recoveries
            ),
            total_unrecoverable=(
                total_unrecoverable
            ),
            total_revenue_at_risk=(
                total_revenue_at_risk
            ),
            total_recovered_revenue=(
                total_recovered_revenue
            ),
            recovery_rate=(
                round(
                    recovery_rate,
                    4,
                )
            ),
            attempts=tuple(
                attempts
            ),
        )