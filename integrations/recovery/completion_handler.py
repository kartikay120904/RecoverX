from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID
from integrations.recovery.payment_link_store import (
    PaymentLinkStore,
    payment_link_store,
)


@dataclass(frozen=True)
class RecoveryCompletionResult:
    """
    Result of processing a verified Razorpay
    recovery completion event.
    """

    processed: bool

    payment_id: UUID | None

    payment_link_id: str | None

    payment_status: str | None

    actual_revenue: Decimal | None

    event_type: str


class RecoveryCompletionHandler:
    """
    Handles verified Razorpay recovery completion events.

    This component is intentionally isolated from
    the existing simulator and recovery logic.
    """

    def __init__(
            self,
            *,
            link_store: PaymentLinkStore | None = None,
        ) -> None:

            self.link_store = (
                link_store
                if link_store is not None
                else payment_link_store
            )

    def process(
        self,
        *,
        event_type: str,
        payment_link_id: str | None,
        payment_id: str | None,
        payment_status: str | None,
        amount: int | None,
    ) -> RecoveryCompletionResult:
        """
        Process a verified Razorpay webhook event.

        Razorpay amounts are received in the smallest
        currency unit. For INR, that means paise.

        A valid payment_link.paid event is considered
        successfully processed even when an internal
        RecoverX payment cannot yet be resolved.
        """

        if event_type != "payment_link.paid":
            return RecoveryCompletionResult(
                processed=False,
                payment_id=None,
                payment_link_id=payment_link_id,
                payment_status=payment_status,
                actual_revenue=None,
                event_type=event_type,
            )

        # -------------------------------------------------
        # Resolve internal RecoverX payment ID
        # -------------------------------------------------

        internal_payment_id: UUID | None = None

        # Preferred path:
        # Resolve through the Razorpay Payment Link mapping.
        if payment_link_id:
            internal_payment_id = (
                self.link_store.get_payment_id(
                    payment_link_id
                )
            )

        # Backward-compatible fallback:
        # Some existing callers/tests provide the internal
        # RecoverX UUID directly through payment_id.
        if (
            internal_payment_id is None
            and payment_id
        ):
            try:
                internal_payment_id = UUID(
                    payment_id
                )
            except (
                TypeError,
                ValueError,
            ):
                internal_payment_id = None

        # -------------------------------------------------
        # Convert paise to INR
        # -------------------------------------------------

        actual_revenue: Decimal | None = None

        if amount is not None:
            actual_revenue = (
                Decimal(amount)
                / Decimal("100")
            )

        # -------------------------------------------------
        # The webhook event itself was successfully handled.
        #
        # Persistence is a separate concern and requires
        # an internal RecoverX payment ID.
        # -------------------------------------------------

        return RecoveryCompletionResult(
            processed=True,
            payment_id=internal_payment_id,
            payment_link_id=payment_link_id,
            payment_status=payment_status,
            actual_revenue=actual_revenue,
            event_type=event_type,
        )