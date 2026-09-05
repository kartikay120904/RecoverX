from decimal import Decimal
from uuid import uuid4

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from simulator.analytics.recovery_metrics import (
    RecoveryPerformanceTracker,
)


def create_attempt(
    strategy: RecoveryStrategy,
    status: RecoveryStatus,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        recovery_id=uuid4(),
        payment_id=uuid4(),
        strategy=strategy,
        predicted_probability=0.8,
        predicted_revenue=Decimal("100"),
        status=status,
    )


def test_successful_recovery_updates_metrics():

    tracker = RecoveryPerformanceTracker()

    attempt = create_attempt(
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStatus.SUCCEEDED,
    )

    tracker.record(attempt)

    performance = tracker.performances[
        RecoveryStrategy.RETRY_PAYMENT
    ]

    assert performance.total_attempts == 1
    assert performance.successful_attempts == 1
    assert performance.failed_attempts == 0
    assert performance.success_rate == 1.0


def test_failed_recovery_updates_metrics():

    tracker = RecoveryPerformanceTracker()

    attempt = create_attempt(
        RecoveryStrategy.RECOVERY_LINK,
        RecoveryStatus.FAILED,
    )

    tracker.record(attempt)

    performance = tracker.performances[
        RecoveryStrategy.RECOVERY_LINK
    ]

    assert performance.total_attempts == 1
    assert performance.successful_attempts == 0
    assert performance.failed_attempts == 1
    assert performance.success_rate == 0.0


def test_non_terminal_recovery_is_not_recorded():

    tracker = RecoveryPerformanceTracker()

    attempt = create_attempt(
        RecoveryStrategy.RETRY_PAYMENT,
        RecoveryStatus.PROPOSED,
    )

    tracker.record(attempt)

    assert tracker.performances == {}


def test_success_rate_for_multiple_attempts():

    tracker = RecoveryPerformanceTracker()

    tracker.record(
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.SUCCEEDED,
        )
    )

    tracker.record(
        create_attempt(
            RecoveryStrategy.RETRY_PAYMENT,
            RecoveryStatus.FAILED,
        )
    )

    assert (
        tracker.get_success_rate(
            RecoveryStrategy.RETRY_PAYMENT
        )
        == 0.5
    )