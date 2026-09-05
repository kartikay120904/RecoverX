from dataclasses import dataclass

from backend.app.domain.enums import (
    PaymentFailureCode,
    RecoveryStrategy,
)
from backend.app.domain.models import Payment


@dataclass(frozen=True)
class FailureDiagnosis:
    """
    Structured diagnosis of a failed payment.

    This converts a raw payment failure code into an
    interpretable root cause and recommended recovery
    strategy.
    """

    category: str

    root_cause: str

    recommended_strategy: RecoveryStrategy

    confidence: float


class PaymentFailureDiagnoser:
    """
    Diagnoses failed payments and recommends an
    appropriate recovery strategy.

    The diagnoser intentionally maps different root
    causes to different interventions instead of using
    a generic retry for every failure.
    """

    def diagnose(
        self,
        payment: Payment,
    ) -> FailureDiagnosis:

        failure_code = payment.failure_code

        if failure_code is None:

            return FailureDiagnosis(
                category="unknown",
                root_cause=(
                    "Payment failed without a "
                    "specific failure code."
                ),
                recommended_strategy=(
                    RecoveryStrategy.NO_ACTION
                ),
                confidence=0.20,
            )

        normalized_code = (
            failure_code.value
            if hasattr(
                failure_code,
                "value",
            )
            else str(
                failure_code
            )
        )

        if (
            normalized_code
            == PaymentFailureCode.BANK_TIMEOUT.value
        ):

            return FailureDiagnosis(
                category="temporary_bank_failure",
                root_cause=(
                    "The issuing bank did not respond "
                    "within the expected time window."
                ),
                recommended_strategy=(
                    RecoveryStrategy.RETRY_PAYMENT
                ),
                confidence=0.95,
            )

        if (
            normalized_code
            == PaymentFailureCode.GATEWAY_TIMEOUT.value
        ):

            return FailureDiagnosis(
                category="temporary_gateway_failure",
                root_cause=(
                    "The payment gateway timed out while "
                    "processing the transaction."
                ),
                recommended_strategy=(
                    RecoveryStrategy.RETRY_PAYMENT
                ),
                confidence=0.95,
            )

        if (
            normalized_code
            == PaymentFailureCode.NETWORK_ERROR.value
        ):

            return FailureDiagnosis(
                category="network_failure",
                root_cause=(
                    "A transient network issue interrupted "
                    "the payment flow."
                ),
                recommended_strategy=(
                    RecoveryStrategy.RETRY_PAYMENT
                ),
                confidence=0.85,
            )

        if (
            normalized_code
            == PaymentFailureCode.INSUFFICIENT_FUNDS.value
        ):

            return FailureDiagnosis(
                category="customer_funds_issue",
                root_cause=(
                    "The customer does not currently have "
                    "sufficient available funds."
                ),
                recommended_strategy=(
                    RecoveryStrategy.SEND_REMINDER
                ),
                confidence=0.90,
            )

        if (
            normalized_code
            == PaymentFailureCode.PAYMENT_DECLINED.value
        ):

            return FailureDiagnosis(
                category="payment_declined",
                root_cause=(
                    "The payment instrument was declined "
                    "by the issuing bank or provider."
                ),
                recommended_strategy=(
                    RecoveryStrategy.RECOVERY_LINK
                ),
                confidence=0.80,
            )

        if (
            normalized_code
            == PaymentFailureCode.AUTHENTICATION_FAILED.value
        ):

            return FailureDiagnosis(
                category="authentication_failure",
                root_cause=(
                    "The customer could not complete the "
                    "required payment authentication."
                ),
                recommended_strategy=(
                    RecoveryStrategy.RECOVERY_LINK
                ),
                confidence=0.90,
            )

        return FailureDiagnosis(
            category="unknown_failure",
            root_cause=(
                "The failure code could not be mapped "
                "to a supported recovery workflow."
            ),
            recommended_strategy=(
                RecoveryStrategy.ESCALATE
            ),
            confidence=0.40,
        )