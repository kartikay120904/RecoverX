from decimal import Decimal
from uuid import uuid4

from integrations.razorpay.client import RazorpayClient
from integrations.razorpay.payment_link_adapter import (
    PaymentLinkRecoveryAdapter,
)


def main() -> None:

    payment_id = uuid4()

    adapter = PaymentLinkRecoveryAdapter(
        client=RazorpayClient()
    )

    result = adapter.create_recovery_link(
        payment_id=payment_id,
        amount=Decimal("100.00"),
        currency="INR",
        description=(
            "RecoverX Test Mode recovery payment"
        ),
    )

    print()

    print("Recovery Payment Link Created")

    print(
        "Payment ID:",
        payment_id,
    )

    print(
        "Payment Link ID:",
        result.payment_link_id,
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

    print(
        "Payment Link:",
        result.short_url,
    )


if __name__ == "__main__":
    main()