from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from random import Random
from uuid import UUID, NAMESPACE_DNS, uuid5

from backend.app.domain.audit import AuditEventType
from backend.app.domain.enums import (
    PaymentStatus,
    RecoveryStatus,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.audit.service import AuditService
from simulator.recovery.executor import RecoveryExecutor
from simulator.recovery.orchestrator import RecoveryOrchestrator


class RecoverySimulationRunner:
    """
    Deterministic recovery simulation runner.

    Responsibilities:

    1. Generate deterministic failed payments.
    2. Record PAYMENT_DETECTED.
    3. Submit payments to the recovery orchestrator.
    4. Record RECOVERY_PROPOSED.
    5. Record RECOVERY_APPROVED.
    6. Execute the recovery attempt.
    7. Record the terminal result.
    8. Return completed recovery attempts.

    Lifecycle ownership:

        Orchestrator:
            proposal / recovery decision / audit events

        Executor:
            executable state
                -> EXECUTING
                -> SUCCEEDED / FAILED

    The runner must never call mark_succeeded() or
    mark_failed() after executor.execute(), because
    the executor already performs the terminal transition.
    """

    FAILURE_CODES = (
        "gateway_timeout",
        "bank_timeout",
        "insufficient_funds",
        "network_error",
        "payment_declined",
    )

    PAYMENT_METHODS = (
        "card",
        "upi",
        "netbanking",
        "wallet",
    )

    CURRENCIES = (
        "INR",
    )

    def __init__(
        self,
        seed: int | None = None,
        orchestrator: RecoveryOrchestrator | None = None,
        executor: RecoveryExecutor | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        """
        Create a deterministic recovery simulation runner.
        """

        self.seed = seed
        self.rng = Random(seed)

        self.audit_service = (
            audit_service
            if audit_service is not None
            else AuditService()
        )

        self.orchestrator = (
            orchestrator
            if orchestrator is not None
            else RecoveryOrchestrator(
                audit_service=self.audit_service,
            )
        )

        self.executor = (
            executor
            if executor is not None
            else RecoveryExecutor()
        )

        self._payment_counter = 0

    # ============================================================
    # PAYMENT GENERATION
    # ============================================================

    def generate_payment(
        self,
        index: int | None = None,
    ) -> Payment:
        """
        Generate a deterministic failed payment.
        """

        if index is None:
            index = self._payment_counter
            self._payment_counter += 1

        payment_id = self._deterministic_uuid(
            f"payment:{self.seed}:{index}"
        )

        order_id = self._deterministic_uuid(
            f"order:{self.seed}:{index}"
        )

        customer_id = self._deterministic_uuid(
            f"customer:{self.seed}:{index}"
        )

        amount = self._generate_amount()

        failure_code = self.rng.choice(
            self.FAILURE_CODES
        )

        method = self.rng.choice(
            self.PAYMENT_METHODS
        )

        currency = self.rng.choice(
            self.CURRENCIES
        )

        now = self._deterministic_timestamp(
            index
        )

        return Payment(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            method=method,
            status=PaymentStatus.FAILED,
            failure_code=failure_code,
            created_at=now,
            updated_at=now,
        )

    # ============================================================
    # MAIN SIMULATION
    # ============================================================

    def run(
        self,
        count: int,
    ) -> list[RecoveryAttempt]:
        """
        Run the recovery simulation.

        Args:
            count:
                Number of completed recovery attempts to simulate.

        Returns:
            Exactly `count` completed recovery attempts.

        Raises:
            ValueError:
                If count is negative.
        """

        if count < 0:
            raise ValueError(
                "Simulation count cannot be negative."
            )

        if count == 0:
            return []

        attempts: list[RecoveryAttempt] = []

        index = 0

        while len(attempts) < count:
            payment = self.generate_payment(
                index=index
            )

            index += 1

            self._record_payment_detected(
                payment
            )

            attempt = self._create_recovery_attempt(
                payment=payment
            )

            if attempt is None:
                continue

            self._record_recovery_proposed(
                attempt
            )

            completed_attempt = self._process_attempt(
                attempt=attempt,
                payment=payment,
            )

            if completed_attempt.status in (
                RecoveryStatus.SUCCEEDED,
                RecoveryStatus.FAILED,
            ):
                attempts.append(
                    completed_attempt
                )

        return attempts

    # ============================================================
    # RECOVERY ATTEMPT CREATION
    # ============================================================

    def _create_recovery_attempt(
        self,
        payment: Payment,
    ) -> RecoveryAttempt:
        """
        Create a recovery proposal.
        """

        attempt = self.orchestrator.propose(
            payment=payment,
        )

        if attempt is None:
            raise ValueError(
                "Recovery orchestrator did not create "
                "a recovery attempt."
            )

        return attempt

    # ============================================================
    # RECOVERY PROCESSING
    # ============================================================

    def _process_attempt(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
    ) -> RecoveryAttempt:
        """
        Process a recovery attempt to a terminal state.

        The executor is responsible for:

            -> EXECUTING
            -> SUCCEEDED / FAILED

        The runner must not perform another terminal state
        transition after executor.execute().
        """

        if attempt.status in (
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        ):
            self._record_terminal_audit_event(
                attempt
            )

            return attempt

        self._record_recovery_approved(
            attempt
        )

        self._record_recovery_scheduled(
            attempt
        )
        self._record_recovery_execution_started(
            attempt=attempt,
        )
        result = self.executor.execute(
            attempt=attempt,
            payment=payment,
            rng=self.rng,
        )

        if result.status in (
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        ):
            self._record_terminal_audit_event(
                result
            )

            return result

        raise ValueError(
            "Recovery attempt could not be processed "
            "to a terminal state. Current status: "
            f"{result.status}."
        )

    # ============================================================
    # AUDIT EVENTS
    # ============================================================

    def _record_payment_detected(
        self,
        payment: Payment,
    ) -> None:
        """
        Record detection of a failed payment.
        """

        self.audit_service.record(
            event_type=AuditEventType.PAYMENT_DETECTED,
            payment_id=payment.payment_id,
            recovery_id=None,
        )

    def _record_recovery_proposed(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        """
        Record creation of a recovery proposal.
        """

        self.audit_service.record(
            event_type=AuditEventType.RECOVERY_PROPOSED,
            payment_id=attempt.payment_id,
            recovery_id=attempt.recovery_id,
        )

    def _record_recovery_approved(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        """
        Record approval of a recovery attempt before execution.
        """

        self.audit_service.record(
            event_type=AuditEventType.RECOVERY_APPROVED,
            payment_id=attempt.payment_id,
            recovery_id=attempt.recovery_id,
        )

    def _record_recovery_scheduled(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        """
        Record scheduling of a recovery attempt.

        The audit lifecycle includes a scheduled event before
        the recovery is executed.
        """

        self.audit_service.record(
            event_type=AuditEventType.RECOVERY_SCHEDULED,
            payment_id=attempt.payment_id,
            recovery_id=attempt.recovery_id,
        )

    def _record_terminal_audit_event(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        """
        Record the terminal recovery event.
        """

        if attempt.status == RecoveryStatus.SUCCEEDED:
            self.audit_service.record(
                event_type=AuditEventType.RECOVERY_SUCCEEDED,
                payment_id=attempt.payment_id,
                recovery_id=attempt.recovery_id,
            )

        elif attempt.status == RecoveryStatus.FAILED:
            self.audit_service.record(
                event_type=AuditEventType.RECOVERY_FAILED,
                payment_id=attempt.payment_id,
                recovery_id=attempt.recovery_id,
            )

    # ============================================================
    # DETERMINISTIC HELPERS
    # ============================================================

    def _generate_amount(
        self,
    ) -> Decimal:
        """
        Generate a deterministic payment amount.
        """

        value = self.rng.randint(
            100,
            100_000,
        )

        return Decimal(
            str(value)
        )

    def _deterministic_timestamp(
        self,
        index: int,
    ) -> datetime:
        """
        Generate a deterministic timestamp.
        """

        base = datetime(
            2025,
            1,
            1,
            tzinfo=timezone.utc,
        )

        seed_value = (
            self.seed
            if self.seed is not None
            else 0
        )

        return (
            base
            + timedelta(
                seconds=(
                    seed_value
                    + index
                )
            )
        )

    def _deterministic_uuid(
        self,
        value: str,
    ) -> UUID:
        """
        Generate a deterministic UUID.
        """

        return uuid5(
            NAMESPACE_DNS,
            value,
        )

    def _record_recovery_execution_started(
        self,
        attempt: RecoveryAttempt,
    ) -> None:
        self.audit_service.record(
            event_type=AuditEventType.RECOVERY_EXECUTION_STARTED,
            payment_id=attempt.payment_id,
            recovery_id=attempt.recovery_id,
        )