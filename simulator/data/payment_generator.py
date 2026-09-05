from decimal import Decimal
from random import Random
from uuid import NAMESPACE_URL, uuid5

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
    PaymentStatus,
)
from backend.app.domain.models import (
    Payment,
)


class PaymentBatchGenerator:
    """
    Generates deterministic synthetic failed payments
    for recovery simulation and batch evaluation.

    The generator intentionally creates a mix of
    recoverable failure causes and retry-limit cases
    so the complete recovery workflow can be tested.
    """

    FAILURE_CODES = (
        PaymentFailureCode.BANK_TIMEOUT,
        PaymentFailureCode.NETWORK_ERROR,
        PaymentFailureCode.GATEWAY_TIMEOUT,
        PaymentFailureCode.INSUFFICIENT_FUNDS,
        PaymentFailureCode.AUTHENTICATION_FAILED,
        PaymentFailureCode.PAYMENT_DECLINED,
    )

    PAYMENT_METHODS = (
        PaymentMethod.UPI,
        PaymentMethod.CARD,
    )

    AMOUNTS = (
        Decimal("500"),
        Decimal("1000"),
        Decimal("1500"),
        Decimal("2000"),
        Decimal("2500"),
        Decimal("5000"),
        Decimal("7500"),
        Decimal("10000"),
    )

    def __init__(
        self,
        *,
        seed: int = 42,
    ) -> None:

        self.seed = seed

        self.rng = Random(
            seed
        )

    def generate(
        self,
        *,
        count: int = 50,
    ) -> list[Payment]:
        """
        Generate a deterministic batch of failed
        payments.

        Raises:
            ValueError:
                If count is less than one.
        """

        if count < 1:
            raise ValueError(
                "Payment batch count must be "
                "at least 1."
            )

        payments: list[
            Payment
        ] = []

        for index in range(count):

            payment = (
                self._create_payment(
                    index=index,
                )
            )

            payments.append(
                payment
            )

        return payments

    def _create_payment(
        self,
        *,
        index: int,
    ) -> Payment:
        """
        Create one deterministic synthetic payment.
        """

        failure_code = (
            self.rng.choice(
                self.FAILURE_CODES
            )
        )

        method = (
            self.rng.choice(
                self.PAYMENT_METHODS
            )
        )

        amount = (
            self.rng.choice(
                self.AMOUNTS
            )
        )

        attempt_number = (
            self._select_attempt_number(
                index=index,
            )
        )

        payment_id = uuid5(
            NAMESPACE_URL,
            (
                "recoverx-payment-"
                f"{self.seed}-"
                f"{index}"
            ),
        )

        order_id = uuid5(
            NAMESPACE_URL,
            (
                "recoverx-order-"
                f"{self.seed}-"
                f"{index}"
            ),
        )

        customer_id = uuid5(
            NAMESPACE_URL,
            (
                "recoverx-customer-"
                f"{self.seed}-"
                f"{index}"
            ),
        )

        return Payment(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            currency="INR",
            method=method,
            status=PaymentStatus.FAILED,
            failure_code=(
                failure_code.value
            ),
            attempt_number=attempt_number,
        )

    def _select_attempt_number(
        self,
        *,
        index: int,
    ) -> int:
        """
        Generate bounded retry histories.

        Every tenth payment is deliberately created
        with an excessive attempt count to exercise
        escalation behavior.
        """

        if index % 10 == 0:

            return 4

        return self.rng.randint(
            1,
            3,
        )