from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class RecoveryWebhookOutcome:
    """
    Represents the business outcome of a verified
    Razorpay webhook event.

    This layer does not modify the existing recovery
    domain models. It only translates Razorpay events
    into a recovery-oriented result.
    """

    handled: bool

    recovery_completed: bool

    payment_link_id: str | None

    razorpay_payment_id: str | None

    recovered_amount: Decimal | None

    currency: str | None

    event_type: str


class RecoveryWebhookHandler:
    """
    Handles verified Razorpay webhook events.

    Only verified webhook payloads should be passed
    to this handler.
    """

    PAYMENT_LINK_PAID_EVENT = (
        "payment_link.paid"
    )

    def handle(
        self,
        payload: dict[str, Any],
    ) -> RecoveryWebhookOutcome:
        """
        Translate a verified Razorpay webhook event
        into a RecoverX recovery outcome.
        """

        event_type = str(
            payload.get("event", "")
        )

        if (
            event_type
            != self.PAYMENT_LINK_PAID_EVENT
        ):
            return RecoveryWebhookOutcome(
                handled=False,
                recovery_completed=False,
                payment_link_id=None,
                razorpay_payment_id=None,
                recovered_amount=None,
                currency=None,
                event_type=event_type,
            )

        payload_data = payload.get(
            "payload",
            {},
        )

        payment_link_data = (
            payload_data
            .get(
                "payment_link",
                {},
            )
            .get(
                "entity",
                {},
            )
        )

        payment_data = (
            payload_data
            .get(
                "payment",
                {},
            )
            .get(
                "entity",
                {},
            )
        )

        amount = payment_link_data.get(
            "amount_paid"
        )

        if amount is None:
            amount = payment_link_data.get(
                "amount"
            )

        recovered_amount = (
            Decimal(str(amount))
            / Decimal("100")
            if amount is not None
            else None
        )

        return RecoveryWebhookOutcome(
            handled=True,
            recovery_completed=True,
            payment_link_id=payment_link_data.get(
                "id"
            ),
            razorpay_payment_id=payment_data.get(
                "id"
            ),
            recovered_amount=recovered_amount,
            currency=payment_link_data.get(
                "currency"
            ),
            event_type=event_type,
        )