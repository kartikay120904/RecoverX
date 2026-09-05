from datetime import (
    datetime,
    timedelta,
    timezone,
)
from decimal import Decimal

from backend.app.domain.enums import (
    RecoveryStatus,
    RecoveryStrategy,
)
from backend.app.domain.models import (
    RecoveryAttempt,
)
from backend.app.services.recovery_sla import (
    calculate_sla_compliance_rate,
    evaluate_recovery_sla,
    find_overdue_recoveries,
)


def create_attempt(
    *,
    status: RecoveryStatus = (
        RecoveryStatus.PROPOSED
    ),
    created_at: datetime | None = None,
) -> RecoveryAttempt:

    return RecoveryAttempt(
        strategy=(
            RecoveryStrategy.RETRY_PAYMENT
        ),
        predicted_probability=0.8,
        predicted_revenue=(
            Decimal("100.00")
        ),
        status=status,
        created_at=(
            created_at
            or datetime.now(
                timezone.utc
            )
        ),
    )


def test_recovery_within_sla():

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=5
            )
        )
    )

    result = evaluate_recovery_sla(
        attempt,
        sla=timedelta(
            minutes=10
        ),
        now=now,
    )

    assert result.overdue is False

    assert (
        result.remaining_seconds
        == 300
    )


def test_recovery_exceeds_sla():

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=15
            )
        )
    )

    result = evaluate_recovery_sla(
        attempt,
        sla=timedelta(
            minutes=10
        ),
        now=now,
    )

    assert result.overdue is True

    assert (
        result.remaining_seconds
        == 0
    )


def test_terminal_recovery_is_not_overdue():

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    attempt = create_attempt(
        status=(
            RecoveryStatus.SUCCEEDED
        ),
        created_at=(
            now
            - timedelta(
                hours=2
            )
        ),
    )

    result = evaluate_recovery_sla(
        attempt,
        sla=timedelta(
            minutes=10
        ),
        now=now,
    )

    assert result.overdue is False


def test_find_overdue_recoveries():

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    overdue_attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=30
            )
        )
    )

    valid_attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=5
            )
        )
    )

    results = find_overdue_recoveries(
        [
            overdue_attempt,
            valid_attempt,
        ],
        sla=timedelta(
            minutes=10
        ),
        now=now,
    )

    assert len(results) == 1

    assert results[0].overdue is True


def test_sla_compliance_rate():

    now = datetime(
        2026,
        1,
        1,
        tzinfo=timezone.utc,
    )

    compliant_attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=5
            )
        )
    )

    overdue_attempt = create_attempt(
        created_at=(
            now
            - timedelta(
                minutes=20
            )
        )
    )

    compliance_rate = (
        calculate_sla_compliance_rate(
            [
                compliant_attempt,
                overdue_attempt,
            ],
            sla=timedelta(
                minutes=10
            ),
            now=now,
        )
    )

    assert (
        compliance_rate
        == 0.5
    )


def test_empty_attempts_have_full_compliance():

    compliance_rate = (
        calculate_sla_compliance_rate(
            [],
            sla=timedelta(
                minutes=10
            ),
        )
    )

    assert (
        compliance_rate
        == 1.0
    )