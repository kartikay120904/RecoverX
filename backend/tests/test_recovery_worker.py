from datetime import (
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal
from random import Random
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

from simulator.recovery.executor import (
    RecoveryExecutor,
)
from simulator.recovery.scheduler import (
    RecoveryScheduler,
)
from simulator.recovery.worker import (
    RecoveryWorker,
)


def create_payment():

    return Payment(
        payment_id=uuid4(),
        order_id=uuid4(),
        customer_id=uuid4(),
        amount=Decimal("100"),
        method=PaymentMethod.UPI,
        status=PaymentStatus.FAILED,
        failure_code="BANK_TIMEOUT",
        attempt_number=1,
    )


def create_attempt(
    payment,
):

    return RecoveryAttempt(
        payment_id=payment.payment_id,
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        predicted_probability=1.0,
        predicted_revenue=Decimal("100"),
        status=RecoveryStatus.APPROVED,
    )


def test_due_recovery_is_processed():

    scheduler = RecoveryScheduler()

    executor = RecoveryExecutor()

    worker = RecoveryWorker(
        scheduler=scheduler,
        executor=executor,
    )

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    schedules = {
        payment.payment_id: schedule
    }

    payments = {
        payment.payment_id: payment
    }

    attempts = {
        payment.payment_id: attempt
    }

    result = worker.process_due(
        schedules=schedules,
        payments=payments,
        attempts=attempts,
        rng=Random(42),
        now=(
            now
            + timedelta(minutes=10)
        ),
    )

    assert result.scanned == 1

    assert result.due == 1

    assert result.executed == 1

    assert len(
        schedules
    ) == 0


def test_future_recovery_is_not_processed():

    scheduler = RecoveryScheduler()

    executor = RecoveryExecutor()

    worker = RecoveryWorker(
        scheduler=scheduler,
        executor=executor,
    )

    payment = create_payment()

    attempt = create_attempt(
        payment
    )

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    schedule = scheduler.schedule(
        attempt,
        now,
    )

    schedules = {
        payment.payment_id: schedule
    }

    payments = {
        payment.payment_id: payment
    }

    attempts = {
        payment.payment_id: attempt
    }

    result = worker.process_due(
        schedules=schedules,
        payments=payments,
        attempts=attempts,
        rng=Random(42),
        now=now,
    )

    assert result.scanned == 1

    assert result.due == 0

    assert result.executed == 0

    assert len(
        schedules
    ) == 1