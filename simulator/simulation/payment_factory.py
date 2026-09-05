from decimal import Decimal
from random import Random
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
)
from backend.app.domain.models import Payment


class SyntheticPaymentFactory:
    """
    Creates deterministic synthetic failed payments
    for batch recovery simulations.

    The factory does not modify production recovery
    components and exists only to generate simulation
    input data.
    """

    FAILURE_CODES = [
        PaymentFailureCode.BANK_TIMEOUT.value,
        PaymentFailureCode.NETWORK_ERROR.value,
        PaymentFailureCode.GATEWAY_TIMEOUT.value,
        PaymentFailureCode.INSUFFICIENT_FUNDS.value,
        PaymentFailureCode.AUTHENTICATION_FAILED.value,
        PaymentFailureCode.PAYMENT_DECLINED.value,
    ]

    METHODS = [
        PaymentMethod.UPI,
        PaymentMethod.CARD,
    ]

    AMOUNTS = [
        Decimal("500"),
        Decimal("1000"),
        Decimal("2500"),
        Decimal("5000"),
        Decimal("10000"),
    ]

    def create_batch(
        self,
        *,
        size: int,
        rng: Random,
    ) -> list[Payment]:
        """
        Create a deterministic batch of synthetic
        failed payments.
        """

        payments: list[Payment] = []

        for _ in range(size):

            payment = Payment(
                payment_id=uuid4(),
                order_id=uuid4(),
                customer_id=uuid4(),
                amount=rng.choice(
                    self.AMOUNTS
                ),
                currency="INR",
                method=rng.choice(
                    self.METHODS
                ),
                status=PaymentStatus.FAILED,
                failure_code=rng.choice(
                    self.FAILURE_CODES
                ),
                attempt_number=rng.randint(
                    1,
                    5,
                ),
            )

            payments.append(
                payment
            )

        return payments