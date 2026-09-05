from decimal import Decimal
from uuid import uuid4

from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryAdapter,
)


def main() -> None:
    """
    Perform one real Razorpay Test Mode
    Payment Link creation.
    """

    adapter = PaymentLinkRecoveryAdapter()

    payment_id = uuid4()

    result = adapter.create_recovery_link(
        payment_id=payment_id,
        amount=Decimal("10.00"),
        currency="INR",
        description=(
            "RecoverX Test Mode Recovery"
        ),
    )

    print()

    print("Razorpay Payment Link Created")

    print(
        "Payment ID:",
        payment_id,
    )

    print(
        "Payment Link ID:",
        result.payment_link_id,
    )

    print(
        "Short URL:",
        result.short_url,
    )

    print(
        "Status:",
        result.status,
    )

    print(
        "Amount:",
        result.amount,
        result.currency,
    )


if __name__ == "__main__":
    main()