from dataclasses import dataclass
from datetime import datetime, timezone
from random import Random
from typing import Callable
from uuid import UUID

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.recovery.executor import (
    RecoveryExecutor,
)
from simulator.recovery.scheduler import (
    RecoverySchedule,
    RecoveryScheduler,
)


@dataclass(frozen=True)
class RecoveryWorkerResult:
    """
    Result produced after processing
    scheduled recovery attempts.
    """

    scanned: int

    due: int

    executed: int

    skipped: int


class RecoveryWorker:
    """
    Processes recovery attempts that have reached
    their scheduled execution time.
    """

    def __init__(
        self,
        scheduler: RecoveryScheduler,
        executor: RecoveryExecutor,
    ) -> None:

        self.scheduler = scheduler
        self.executor = executor

    def process_due(
        self,
        schedules: dict[
            UUID,
            RecoverySchedule,
        ],
        payments: dict[
            UUID,
            Payment,
        ],
        attempts: dict[
            UUID,
            RecoveryAttempt,
        ],
        rng: Random,
        now: datetime | None = None,
        on_executed: Callable[
            [Payment, RecoveryAttempt],
            None,
        ]
        | None = None,
    ) -> RecoveryWorkerResult:
        """
        Execute every scheduled recovery attempt
        that is currently due.
        """

        if now is None:

            now = datetime.now(
                timezone.utc
            )

        scanned = len(
            schedules
        )

        due = 0
        executed = 0
        skipped = 0

        due_payment_ids = []

        for (
            payment_id,
            schedule,
        ) in schedules.items():

            if not self.scheduler.is_due(
                schedule,
                now,
            ):

                continue

            due += 1

            payment = payments.get(
                payment_id
            )

            attempt = attempts.get(
                payment_id
            )

            if (
                payment is None
                or attempt is None
            ):

                skipped += 1

                due_payment_ids.append(
                    payment_id
                )

                continue

            updated_attempt = (
                self.executor.execute(
                    attempt=attempt,
                    payment=payment,
                    rng=rng,
                )
            )

            attempts[
                payment_id
            ] = updated_attempt

            executed += 1

            due_payment_ids.append(
                payment_id
            )

            if on_executed is not None:

                on_executed(
                    payment,
                    updated_attempt,
                )

        # ---------------------------------------------
        # Remove processed schedules
        # ---------------------------------------------

        for payment_id in due_payment_ids:

            schedules.pop(
                payment_id,
                None,
            )

        return RecoveryWorkerResult(
            scanned=scanned,
            due=due,
            executed=executed,
            skipped=skipped,
        )