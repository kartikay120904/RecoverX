"""
Razorpay Test Mode integration for RecoverX.

This module:
- Loads Razorpay credentials from backend/.env
- Ensures only Razorpay Test Mode keys are accepted
- Creates Razorpay orders
- Verifies Razorpay checkout signatures
"""

import os
from pathlib import Path
from typing import Any

import razorpay
from dotenv import load_dotenv


# =========================================================
# Environment configuration
# =========================================================

# Project structure:
#
# recoverx/
# ├── backend/
# │   ├── .env
# │   └── app/
# │       └── services/
# │           └── razorpay_service.py
#
# From this file:
# parents[0] = services
# parents[1] = app
# parents[2] = backend
# parents[3] = recoverx

BACKEND_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = BACKEND_ROOT / ".env"

load_dotenv(ENV_FILE)


# =========================================================
# Razorpay Service
# =========================================================

class RazorpayService:
    """
    Service wrapper around the Razorpay Python SDK.

    RecoverX intentionally supports Razorpay TEST MODE only.
    Live credentials are rejected.
    """

    def __init__(self) -> None:
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not self.key_id or not self.key_secret:
            raise RuntimeError(
                "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
                "must be configured in backend/.env"
            )

        # Safety check:
        # RecoverX must never accidentally use live credentials.
        if self.key_id.startswith("rzp_live_"):
            raise RuntimeError(
                "Live Razorpay credentials are not allowed. "
                "Use Razorpay TEST MODE credentials "
                "(rzp_test_...)."
            )

        if not self.key_id.startswith("rzp_test_"):
            raise RuntimeError(
                "Invalid Razorpay Key ID. "
                "RecoverX requires a Razorpay TEST MODE key "
                "starting with 'rzp_test_'."
            )

        self.client = razorpay.Client(
            auth=(self.key_id, self.key_secret)
        )

    # =====================================================
    # Create Razorpay Order
    # =====================================================

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str | None = None,
        notes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a Razorpay order.

        Parameters
        ----------
        amount:
            Amount in the smallest currency unit.
            For INR, this means paise.

            Example:
                ₹100 = 10000 paise

        currency:
            Currency code. Defaults to INR.

        receipt:
            Optional internal receipt/reference ID.

        notes:
            Optional metadata attached to the order.

        Returns
        -------
        dict
            Razorpay order response.
        """

        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        order_data: dict[str, Any] = {
            "amount": amount,
            "currency": currency,
        }

        if receipt:
            order_data["receipt"] = receipt

        if notes:
            order_data["notes"] = notes

        return self.client.order.create(order_data)

    # =====================================================
    # Verify Razorpay Checkout Signature
    # =====================================================

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verify the signature returned by Razorpay Checkout.

        Returns True when the payment signature is valid.

        Raises
        ------
        razorpay.errors.SignatureVerificationError
            If the signature is invalid.
        """

        payment_data = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
            self.client.utility.verify_payment_signature(
                payment_data
            )
            return True

        except razorpay.errors.SignatureVerificationError:
            return False

    # =====================================================
    # Fetch Order
    # =====================================================

    def fetch_order(self, order_id: str) -> dict[str, Any]:
        """
        Fetch an existing Razorpay order.
        """

        return self.client.order.fetch(order_id)

    # =====================================================
    # Fetch Payment
    # =====================================================

    def fetch_payment(self, payment_id: str) -> dict[str, Any]:
        """
        Fetch an existing Razorpay payment.
        """

        return self.client.payment.fetch(payment_id)

    # =====================================================
    # Capture Payment
    # =====================================================

    def capture_payment(
        self,
        payment_id: str,
        amount: int,
        currency: str = "INR",
    ) -> dict[str, Any]:
        """
        Capture a Razorpay payment.

        Amount is specified in the smallest currency unit.
        For INR, amount is in paise.
        """

        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        return self.client.payment.capture(
            payment_id,
            amount,
            {
                "currency": currency,
            },
        )

    # =====================================================
    # Refund Payment
    # =====================================================

    def refund_payment(
        self,
        payment_id: str,
        amount: int | None = None,
    ) -> dict[str, Any]:
        """
        Refund a Razorpay payment.

        If amount is None, Razorpay processes a full refund.
        Otherwise amount is in the smallest currency unit.
        """

        if amount is not None and amount <= 0:
            raise ValueError("Refund amount must be greater than zero.")

        if amount is None:
            return self.client.payment.refund(payment_id)

        return self.client.payment.refund(
            payment_id,
            {
                "amount": amount,
            },
        )


# =========================================================
# Singleton service instance
# =========================================================

razorpay_service = RazorpayService()