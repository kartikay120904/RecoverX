from decimal import Decimal
from random import Random

from backend.app.domain.enums import RecoveryStatus, RecoveryStrategy
from backend.app.domain.models import Payment, RecoveryAttempt


class RecoveryExecutor:
    """
    Executes a proposed recovery attempt and records its outcome.
    """

    def execute(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
        rng: Random,
    ) -> RecoveryAttempt:

        if attempt.status != RecoveryStatus.PROPOSED:
            raise ValueError(
                "Only proposed recovery attempts can be executed."
            )

        attempt.status = RecoveryStatus.APPROVED

        success = rng.random() < attempt.predicted_probability

        attempt.status = (
            RecoveryStatus.SUCCEEDED
            if success
            else RecoveryStatus.FAILED
        )

        attempt.actual_revenue = (
            payment.amount
            if success
            else Decimal("0")
        )

        return attempt