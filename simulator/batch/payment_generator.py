from random import Random
from uuid import UUID

from backend.app.domain.models import (
    Payment,
)


class PaymentGenerator:
    """
    Generates deterministic synthetic payment data
    for RecoverX batch simulations.

    This generator is intentionally independent from
    recovery, policy, escalation, and execution logic.
    """

    FAILURE_CODES = (
        "bank_timeout",
        "insufficient_funds",
        "card_expired",
        "otp_failed",
        "bank_unavailable",
    )

    PAYMENT_METHODS = (
        "card",
        "upi",
        "netbanking",
    )

    def generate(
        self,
        *,
        count: int,
        rng: Random,
    ) -> list[Payment]:
        """
        Generate a deterministic batch of synthetic
        payments.

        The supplied Random instance allows tests and
        demos to be reproduced exactly.
        """

        if count < 0:
            raise ValueError(
                "count must be greater than or equal to zero."
            )

        payments: list[Payment] = []

        for index in range(1, count + 1):

            payment = Payment(
                payment_id=UUID(
                    f"00000000-0000-0000-0000-"
                    f"{index:012d}"
                ),
                amount=self._generate_amount(
                    rng=rng,
                ),
                method=rng.choice(
                    self.PAYMENT_METHODS
                ),
                failure_code=rng.choice(
                    self.FAILURE_CODES
                ),
            )

            payments.append(
                payment
            )

        return payments

    def _generate_amount(
        self,
        *,
        rng: Random,
    ) -> float:
        """
        Generate a realistic synthetic payment amount.
        """

        return float(
            rng.randint(
                100,
                50000,
            )
        )