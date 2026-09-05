from dataclasses import dataclass
import hashlib
import hmac
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


@dataclass(frozen=True)
class RecoveryWebhookResult:
    """
    Normalized result of processing a Razorpay
    Payment Link webhook.
    """

    verified: bool

    event_type: str | None

    payment_link_id: str | None

    reference_id: str | None

    payment_id: str | None

    payment_status: str | None

    amount: int | None

    currency: str | None

    raw_payload: dict[str, Any] | None = None

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = (
    PROJECT_ROOT
    / "backend"
    / ".env"
)

load_dotenv(ENV_FILE)

class RazorpayWebhookVerifier:
    """
    Verifies Razorpay webhook signatures and
    extracts recovery-related Payment Link data.

    This component is intentionally isolated from
    FastAPI, simulator, and recovery orchestration.
    """

    def __init__(
        self,
        *,
        webhook_secret: str | None = None,
    ) -> None:

        self.webhook_secret = (
            webhook_secret
            if webhook_secret is not None
            else os.getenv(
                "RAZORPAY_WEBHOOK_SECRET"
            )
        )

        if not self.webhook_secret:
            raise RuntimeError(
                "RAZORPAY_WEBHOOK_SECRET "
                "is not configured"
            )

    def verify_signature(
        self,
        *,
        raw_body: bytes,
        signature: str,
    ) -> bool:
        """
        Verify the Razorpay webhook signature.

        The raw request body must be used exactly
        as received.
        """

        expected_signature = hmac.new(
            self.webhook_secret.encode(
                "utf-8"
            ),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            expected_signature,
            signature,
        )

    def process(
        self,
        *,
        raw_body: bytes,
        signature: str,
        payload: dict[str, Any],
    ) -> RecoveryWebhookResult:
        """
        Verify and normalize a Razorpay webhook.
        """

        verified = self.verify_signature(
            raw_body=raw_body,
            signature=signature,
        )

        if not verified:
            return RecoveryWebhookResult(
                verified=False,
                event_type=None,
                payment_link_id=None,
                payment_id=None,
                payment_status=None,
                amount=None,
                currency=None,
                reference_id=None,
                raw_payload=None,
            )

        event_type = payload.get(
            "event"
        )

        payment_link_entity = (
            payload
            .get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
        )

        payment_entity = (
            payload
            .get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        return RecoveryWebhookResult(
            verified=True,
            event_type=event_type,
            payment_link_id=(
                payment_link_entity.get(
                    "id"
                )
            ),
            reference_id=(
                payment_link_entity.get(
                    "reference_id"
                )
            ),
            payment_id=(
                payment_entity.get(
                    "id"
                )
            ),
            payment_status=(
                payment_link_entity.get(
                    "status"
                )
            ),
            amount=(
                payment_link_entity.get(
                    "amount"
                )
            ),
            currency=(
                payment_link_entity.get(
                    "currency"
                )
            ),
            raw_payload=payload,
        )