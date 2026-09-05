from enum import Enum


# =========================================================
# Payment Enums
# =========================================================

class PaymentStatus(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    RETRY_ELIGIBLE = "retry_eligible"
    RETRYING = "retrying"
    REFUNDED = "refunded"
    SUCCEEDED = "succeeded"

class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class PaymentFailureCode(str, Enum):
    INSUFFICIENT_FUNDS = "insufficient_funds"
    BANK_TIMEOUT = "bank_timeout"
    NETWORK_ERROR = "network_error"
    PAYMENT_DECLINED = "payment_declined"
    AUTHENTICATION_FAILED = "authentication_failed"
    GATEWAY_TIMEOUT = "gateway_timeout"


# =========================================================
# Order Enums
# =========================================================

class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


# =========================================================
# Recovery Decision Enums
# =========================================================

class RecoveryStrategy(str, Enum):
    RETRY_PAYMENT = "retry_payment"
    SEND_REMINDER = "send_reminder"
    RECOVERY_LINK = "recovery_link"
    INCENTIVE = "incentive"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


# =========================================================
# Recovery Lifecycle Enums
# =========================================================

class RecoveryStatus(str, Enum):
    """
    Complete recovery lifecycle.

    This enum intentionally supports both:
    - recovery decision / approval workflows
    - scheduled recovery execution workflows
    """

    # Initial decision state
    PROPOSED = "proposed"

    # Decision workflow
    APPROVED = "approved"
    REJECTED = "rejected"

    # Scheduling workflow
    SCHEDULED = "scheduled"

    # Execution workflow
    EXECUTING = "executing"

    # Successful terminal state
    SUCCEEDED = "succeeded"

    # Failed terminal state
    FAILED = "failed"

    # Manually or automatically cancelled
    CANCELLED = "cancelled"