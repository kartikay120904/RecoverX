from enum import Enum


class PaymentStatus(str, Enum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    RETRY_ELIGIBLE = "retry_eligible"
    RETRYING = "retrying"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"


class OrderStatus(str, Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class RecoveryStrategy(str, Enum):
    RETRY_PAYMENT = "retry_payment"
    SEND_REMINDER = "send_reminder"
    RECOVERY_LINK = "recovery_link"
    INCENTIVE = "incentive"
    ESCALATE = "escalate"
    NO_ACTION = "no_action"


class RecoveryStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    SUCCEEDED = "succeeded"
    FAILED = "failed"