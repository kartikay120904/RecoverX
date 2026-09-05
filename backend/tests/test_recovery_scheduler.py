from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    PaymentMethod,
    PaymentStatus,
    RecoveryStatus,
    RecoveryStrategy,
)

from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from simulator.recovery.scheduler import (
    RecoveryScheduler,
)


def create_attempt(
    strategy: RecoveryStrategy,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        payment_id=uuid4(),
        strategy=strategy,
        predicted_probability=0.7,
        predicted_revenue=Decimal("100"),
        status=RecoveryStatus.PROPOSED,
    )


def test_retry_payment_schedule():

    scheduler = RecoveryScheduler()

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        RecoveryStrategy.RETRY_PAYMENT
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    assert (
        schedule.scheduled_at
        == now + timedelta(minutes=5)
    )


def test_reminder_schedule():

    scheduler = RecoveryScheduler()

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        RecoveryStrategy.SEND_REMINDER
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    assert (
        schedule.scheduled_at
        == now + timedelta(hours=1)
    )


def test_schedule_not_due_before_time():

    scheduler = RecoveryScheduler()

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        RecoveryStrategy.RETRY_PAYMENT
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    assert (
        scheduler.is_due(
            schedule,
            now,
        )
        is False
    )


def test_schedule_due_after_time():

    scheduler = RecoveryScheduler()

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        RecoveryStrategy.RETRY_PAYMENT
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    future = (
        now
        + timedelta(minutes=6)
    )

    assert (
        scheduler.is_due(
            schedule,
            future,
        )
        is True
    )  