from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from integrations.recovery.completion_handler import (
    RecoveryCompletionHandler,
)
from integrations.recovery.webhook_verifier import (
    RazorpayWebhookVerifier,
)
from integrations.recovery.recovery_store import (
    recovery_store,
)


router = APIRouter(
    prefix="/webhooks",
    tags=["Razorpay Webhooks"],
)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
) -> dict[str, Any]:
    """
    Receive, verify, and process Razorpay
    recovery webhook events.

    The raw request body is preserved for
    signature verification.
    """

    raw_body = await request.body()

    signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing X-Razorpay-Signature header"
            ),
        )

    try:
        payload = await request.json()

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        ) from exc

    verifier = RazorpayWebhookVerifier()

    verification_result = verifier.process(
        raw_body=raw_body,
        signature=signature,
        payload=payload,
    )

    if not verification_result.verified:
        raise HTTPException(
            status_code=400,
            detail="Invalid Razorpay webhook signature",
        )

    completion_handler = RecoveryCompletionHandler()

    completion_result = completion_handler.process(
        event_type=verification_result.event_type,
        payment_link_id=(
            verification_result.payment_link_id
        ),
        payment_id=(
            verification_result.reference_id
            or verification_result.payment_id
        ),
        payment_status=(
            verification_result.payment_status
        ),
        amount=extract_payment_link_amount(
            payload
        ),
    )

    persisted_recovery = None

    if (
        completion_result.processed
        and completion_result.payment_id is not None
        and completion_result.actual_revenue is not None
    ):
        persisted_recovery = (
            recovery_store.complete_recovery(
                payment_id=completion_result.payment_id,
                actual_revenue=(
                    completion_result.actual_revenue
                ),
                payment_link_id=(
                    completion_result.payment_link_id
                ),
            )
        )

    return {
    "received": True,
    "verified": verification_result.verified,
    "event_type": verification_result.event_type,

    # Existing recovery-oriented fields
    "recovery_processed": (
        completion_result.processed
    ),
    "recovery_persisted": (
        persisted_recovery is not None
    ),
    "actual_revenue": (
        str(completion_result.actual_revenue)
        if completion_result.actual_revenue
        is not None
        else None
    ),

    # Compatibility/API fields
    "handled": (
        completion_result.processed
    ),
    "recovery_completed": (
        persisted_recovery is not None
    ),
    "payment_link_id": (
        verification_result.payment_link_id
    ),
    "razorpay_payment_id": (
        verification_result.payment_id
    ),
    "recovered_amount": (
        str(completion_result.actual_revenue)
        if completion_result.actual_revenue
        is not None
        else None
    ),
    "currency": verification_result.currency,

    # Existing normalized fields
    "payment_id": (
        verification_result.payment_id
    ),
    "payment_status": (
        verification_result.payment_status
    ),
}


def extract_payment_link_amount(
    payload: dict[str, Any],
) -> int | None:
    """
    Extract Payment Link amount from a Razorpay
    webhook payload.

    The amount is returned in the smallest
    currency unit.
    """

    try:
        amount = (
            payload
            .get("payload", {})
            .get("payment_link", {})
            .get("entity", {})
            .get("amount")
        )

        if amount is None:
            return None

        return int(amount)

    except (
        TypeError,
        ValueError,
    ):
        return None