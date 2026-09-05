from dataclasses import dataclass
from random import Random

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.recovery.engine import (
    RecoveryEngine,
)

from simulator.recovery.executor import (
    RecoveryExecutor,
)


@dataclass(frozen=True)
class RecoveryExecutionResult:
    """
    Result of executing the recovery lifecycle
    for a single payment.
    """

    payment: Payment
    attempt: RecoveryAttempt | None


class RecoveryExecutionPipeline:
    """
    Orchestrates recovery proposal and execution
    for a single payment.

    Existing recovery components remain unchanged.
    """

    def __init__(
        self,
        *,
        engine: RecoveryEngine | None = None,
        executor: RecoveryExecutor | None = None,
    ) -> None:

        self._engine = (
            engine
            or RecoveryEngine()
        )

        self._executor = (
            executor
            or RecoveryExecutor()
        )

    def run(
        self,
        *,
        payment: Payment,
        rng: Random | None = None,
    ) -> RecoveryExecutionResult:
        """
        Propose and execute recovery for
        a single payment.
        """

        attempt = (
            self._engine.propose(
                payment
            )
        )

        if attempt is None:
            return RecoveryExecutionResult(
                payment=payment,
                attempt=None,
            )

        executed_attempt = (
            self._executor.execute(
                attempt=attempt,
                payment=payment,
                rng=rng,
            )
        )

        return RecoveryExecutionResult(
            payment=payment,
            attempt=executed_attempt,
        )