from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class PaymentLinkStore:
    """
    Stores the relationship between a RecoverX
    payment ID and a Razorpay Payment Link ID.

    This allows webhook events from Razorpay to
    be mapped back to the internal recovery
    workflow.
    """

    payment_links: dict[str, UUID] = field(
        default_factory=dict
    )

    def register(
        self,
        *,
        payment_link_id: str,
        payment_id: UUID,
    ) -> None:
        """
        Register a Razorpay Payment Link against
        an internal RecoverX payment ID.
        """

        self.payment_links[
            payment_link_id
        ] = payment_id

    def get_payment_id(
        self,
        payment_link_id: str,
    ) -> UUID | None:
        """
        Return the RecoverX payment ID associated
        with a Razorpay Payment Link.
        """

        return self.payment_links.get(
            payment_link_id
        )


# =========================================================
# Shared Payment Link mapping store
# =========================================================

payment_link_store = PaymentLinkStore()