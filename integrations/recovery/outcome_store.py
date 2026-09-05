from dataclasses import dataclass
from decimal import Decimal
from threading import Lock


@dataclass(frozen=True)
class StoredRecoveryOutcome:
    """
    Represents a verified and completed recovery
    stored for operational reporting.

    This model is intentionally isolated from the
    existing RecoverX domain models.
    """

    payment_link_id: str

    razorpay_payment_id: str | None

    recovered_amount: Decimal

    currency: str


class RecoveryOutcomeStore:
    """
    Thread-safe in-memory store for completed
    Razorpay recovery outcomes.

    This store is intentionally isolated so existing
    simulator and domain persistence remain unchanged.
    """

    def __init__(self) -> None:
        self._outcomes: dict[
            str,
            StoredRecoveryOutcome
        ] = {}

        self._lock = Lock()

    def record(
        self,
        outcome: StoredRecoveryOutcome,
    ) -> StoredRecoveryOutcome:
        """
        Store a completed recovery outcome.

        The payment link ID acts as an idempotency key.
        Repeated webhook deliveries for the same
        payment link do not create duplicate records.
        """

        with self._lock:
            existing = self._outcomes.get(
                outcome.payment_link_id
            )

            if existing is not None:
                return existing

            self._outcomes[
                outcome.payment_link_id
            ] = outcome

            return outcome

    def get(
        self,
        payment_link_id: str,
    ) -> StoredRecoveryOutcome | None:
        """
        Retrieve a completed recovery outcome.
        """

        with self._lock:
            return self._outcomes.get(
                payment_link_id
            )

    def all(
        self,
    ) -> list[StoredRecoveryOutcome]:
        """
        Return all stored recovery outcomes.
        """

        with self._lock:
            return list(
                self._outcomes.values()
            )

    def count(self) -> int:
        """
        Return the number of unique completed
        recovery outcomes.
        """

        with self._lock:
            return len(
                self._outcomes
            )

    def total_recovered_amount(
        self,
        currency: str = "INR",
    ) -> Decimal:
        """
        Calculate total recovered revenue for a
        specific currency.
        """

        with self._lock:
            return sum(
                (
                    outcome.recovered_amount
                    for outcome
                    in self._outcomes.values()
                    if outcome.currency
                    == currency
                ),
                start=Decimal("0"),
            )