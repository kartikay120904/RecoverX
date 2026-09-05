from decimal import Decimal
from random import Random

from backend.app.domain.enums import RecoveryStatus
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)
from backend.app.domain.state_machine import (
    InvalidRecoveryTransition,
    transition_recovery,
)

from simulator.recovery.guardrails import (
    RecoveryGuardrails,
)


class RecoveryExecutor:
    """
    Executes recovery attempts through a bounded,
    guardrail-controlled recovery workflow.

    Supported executable states:

        PROPOSED
            -> EXECUTING
            -> SUCCEEDED / FAILED

        APPROVED
            -> EXECUTING
            -> SUCCEEDED / FAILED

        SCHEDULED
            -> EXECUTING
            -> SUCCEEDED / FAILED

        EXECUTING
            -> SUCCEEDED / FAILED
    """

    EXECUTABLE_STATUSES = {
        RecoveryStatus.PROPOSED,
        RecoveryStatus.APPROVED,
        RecoveryStatus.SCHEDULED,
        RecoveryStatus.EXECUTING,
    }

    def __init__(
        self,
        guardrails: RecoveryGuardrails | None = None,
    ) -> None:

        self.guardrails = (
            guardrails
            if guardrails is not None
            else RecoveryGuardrails()
        )

    def execute(
        self,
        attempt: RecoveryAttempt,
        payment: Payment,
        rng: Random,
    ) -> RecoveryAttempt:
        """
        Execute a recovery attempt.
        """

        # ---------------------------------------------
        # Validate lifecycle state
        # ---------------------------------------------

        if (
            attempt.status
            not in self.EXECUTABLE_STATUSES
        ):

            raise ValueError(
                "Only proposed recovery attempts "
                "can be executed"
            )

        # ---------------------------------------------
        # Evaluate guardrails
        # ---------------------------------------------

        decision = (
            self.guardrails.evaluate(
                payment=payment,
                attempt=attempt,
            )
        )

        # ---------------------------------------------
        # Guardrail blocked
        #
        # Every execution path must terminate.
        # ---------------------------------------------

        if not decision.allowed:

            attempt.actual_revenue = Decimal(
                "0"
            )

            if (
                attempt.status
                != RecoveryStatus.EXECUTING
            ):

                try:

                    transition_recovery(
                        attempt,
                        RecoveryStatus.EXECUTING,
                        actor="recovery_executor",
                    )

                except InvalidRecoveryTransition as exc:

                    raise RuntimeError(
                        "Unable to transition blocked "
                        "recovery attempt into EXECUTING."
                    ) from exc

            try:

                transition_recovery(
                    attempt,
                    RecoveryStatus.FAILED,
                    actor="recovery_executor",
                )

            except InvalidRecoveryTransition as exc:

                raise RuntimeError(
                    "Unable to terminate blocked "
                    "recovery attempt as FAILED."
                ) from exc

            return attempt

        # ---------------------------------------------
        # Transition into EXECUTING
        # ---------------------------------------------

        if (
            attempt.status
            != RecoveryStatus.EXECUTING
        ):

            try:

                transition_recovery(
                    attempt,
                    RecoveryStatus.EXECUTING,
                    actor="recovery_executor",
                )

            except InvalidRecoveryTransition as exc:

                raise RuntimeError(
                    "Unable to transition recovery "
                    "attempt into EXECUTING."
                ) from exc

        # ---------------------------------------------
        # Simulate recovery outcome
        # ---------------------------------------------

        probability = (
            attempt.predicted_probability
        )

        success = (
            rng.random()
            < probability
        )

        # ---------------------------------------------
        # Successful recovery
        # ---------------------------------------------

        if success:

            try:

                transition_recovery(
                    attempt,
                    RecoveryStatus.SUCCEEDED,
                    actor="recovery_executor",
                )

            except InvalidRecoveryTransition as exc:

                raise RuntimeError(
                    "Unable to transition recovery "
                    "attempt to SUCCEEDED."
                ) from exc

            attempt.actual_revenue = (
                payment.amount
            )

            return attempt

        # ---------------------------------------------
        # Failed recovery
        # ---------------------------------------------

        try:

            transition_recovery(
                attempt,
                RecoveryStatus.FAILED,
                actor="recovery_executor",
            )

        except InvalidRecoveryTransition as exc:

            raise RuntimeError(
                "Unable to transition recovery "
                "attempt to FAILED."
            ) from exc

        attempt.actual_revenue = Decimal(
            "0"
        )

        return attempt