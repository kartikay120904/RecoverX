from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.app.domain.enums import RecoveryStrategy
from backend.app.domain.models import RecoveryAttempt


@dataclass(frozen=True)
class RecoverySchedule:
    """
    Represents when a recovery attempt should
    be executed.
    """

    recovery_id: str

    payment_id: str

    strategy: RecoveryStrategy

    scheduled_at: datetime

    reason: str


class RecoveryScheduler:
    """
    Determines when recovery actions should
    be executed.

    Different recovery strategies use different
    execution delays.
    """

    def schedule(
        self,
        attempt: RecoveryAttempt,
        now: datetime | None = None,
    ) -> RecoverySchedule:

        if now is None:
            now = datetime.now(
                timezone.utc
            )

        delay = self._get_delay(
            attempt.strategy
        )

        scheduled_at = (
            now + delay
        )

        return RecoverySchedule(
            recovery_id=str(
                attempt.recovery_id
            ),
            payment_id=str(
                attempt.payment_id
            ),
            strategy=attempt.strategy,
            scheduled_at=scheduled_at,
            reason=self._build_reason(
                attempt.strategy,
                delay,
            ),
        )

    def is_due(
        self,
        schedule: RecoverySchedule,
        now: datetime | None = None,
    ) -> bool:

        if now is None:
            now = datetime.now(
                timezone.utc
            )

        return (
            now >= schedule.scheduled_at
        )

    def _get_delay(
        self,
        strategy: RecoveryStrategy,
    ) -> timedelta:

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):

            return timedelta(
                minutes=5
            )

        if (
            strategy
            == RecoveryStrategy.SEND_REMINDER
        ):

            return timedelta(
                hours=1
            )

        if (
            strategy
            == RecoveryStrategy.RECOVERY_LINK
        ):

            return timedelta(
                minutes=15
            )

        if (
            strategy
            == RecoveryStrategy.INCENTIVE
        ):

            return timedelta(
                hours=2
            )

        if (
            strategy
            == RecoveryStrategy.ESCALATE
        ):

            return timedelta(
                days=36500
            )

        return timedelta(
            days=36500
        )

    def _build_reason(
        self,
        strategy: RecoveryStrategy,
        delay: timedelta,
    ) -> str:

        if (
            strategy
            == RecoveryStrategy.RETRY_PAYMENT
        ):

            return (
                "Retry payment scheduled after "
                "a short cooldown period."
            )

        if (
            strategy
            == RecoveryStrategy.SEND_REMINDER
        ):

            return (
                "Customer reminder scheduled "
                "for a later recovery window."
            )

        if (
            strategy
            == RecoveryStrategy.RECOVERY_LINK
        ):

            return (
                "Recovery link scheduled for "
                "customer follow-up."
            )

        if (
            strategy
            == RecoveryStrategy.INCENTIVE
        ):

            return (
                "Incentive recovery action "
                "scheduled for later execution."
            )

        return (
            "Strategy requires manual handling "
            "and is not scheduled for automatic execution."
        )