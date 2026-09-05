import os

import razorpay

from dotenv import load_dotenv


load_dotenv()


class RazorpayClient:
    """
    Thin wrapper around the official Razorpay
    Python SDK.

    This layer isolates Razorpay SDK usage from
    the domain and simulator layers.
    """

    def __init__(self) -> None:

        key_id = os.getenv(
            "RAZORPAY_KEY_ID"
        )

        key_secret = os.getenv(
            "RAZORPAY_KEY_SECRET"
        )

        if not key_id:
            raise RuntimeError(
                "RAZORPAY_KEY_ID is not configured"
            )

        if not key_secret:
            raise RuntimeError(
                "RAZORPAY_KEY_SECRET is not configured"
            )

        if not key_id.startswith(
            "rzp_test_"
        ):
            raise RuntimeError(
                "Only Razorpay Test Mode keys "
                "are allowed for this integration"
            )

        self.client = razorpay.Client(
            auth=(
                key_id,
                key_secret,
            )
        )