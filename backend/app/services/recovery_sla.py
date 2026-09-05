from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from backend.app.domain.enums import RecoveryStatus
from backend.app.domain.models import RecoveryAttempt


@dataclass(frozen=True)
class RecoverySLAResult:
    """
    SLA evaluation result for a recovery attempt.
    """

    recovery_id: str

    status: RecoveryStatus

    age_seconds: float

    sla_seconds: float

    overdue: bool

    remaining_seconds: float

    reason: str


def utc_now() -> datetime:
    """
    Return the current UTC timestamp.
    """

    return datetime.now(
        timezone.utc
    )


def is_terminal_status(
    status: RecoveryStatus,
) -> bool:
    """
    Determine whether a recovery lifecycle
    status is terminal.
    """

    return status in {
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
        RecoveryStatus.CANCELLED,
        RecoveryStatus.REJECTED,
    }


def evaluate_recovery_sla(
    attempt: RecoveryAttempt,
    *,
    sla: timedelta,
    now: datetime | None = None,
) -> RecoverySLAResult:
    """
    Evaluate whether a recovery attempt has
    exceeded its configured SLA.

    Terminal recovery attempts are never
    considered overdue.
    """

    evaluation_time = (
        now
        or utc_now()
    )

    age = (
        evaluation_time
        - attempt.created_at
    )

    age_seconds = max(
        0.0,
        age.total_seconds(),
    )

    sla_seconds = max(
        0.0,
        sla.total_seconds(),
    )

    remaining_seconds = (
        sla_seconds
        - age_seconds
    )

    if is_terminal_status(
        attempt.status,
    ):

        return RecoverySLAResult(
            recovery_id=str(
                attempt.recovery_id
            ),
            status=attempt.status,
            age_seconds=age_seconds,
            sla_seconds=sla_seconds,
            overdue=False,
            remaining_seconds=max(
                0.0,
                remaining_seconds,
            ),
            reason=(
                "Recovery is already in a "
                "terminal state."
            ),
        )

    overdue = (
        age_seconds
        > sla_seconds
    )

    if overdue:

        return RecoverySLAResult(
            recovery_id=str(
                attempt.recovery_id
            ),
            status=attempt.status,
            age_seconds=age_seconds,
            sla_seconds=sla_seconds,
            overdue=True,
            remaining_seconds=0.0,
            reason=(
                "Recovery attempt has exceeded "
                "its SLA."
            ),
        )

    return RecoverySLAResult(
        recovery_id=str(
            attempt.recovery_id
        ),
        status=attempt.status,
        age_seconds=age_seconds,
        sla_seconds=sla_seconds,
        overdue=False,
        remaining_seconds=remaining_seconds,
        reason=(
            "Recovery attempt is within "
            "its SLA."
        ),
    )


def find_overdue_recoveries(
    attempts: Iterable[
        RecoveryAttempt
    ],
    *,
    sla: timedelta,
    now: datetime | None = None,
) -> list[RecoverySLAResult]:
    """
    Return SLA results for all overdue
    recovery attempts.
    """

    results = []

    for attempt in attempts:

        result = evaluate_recovery_sla(
            attempt,
            sla=sla,
            now=now,
        )

        if result.overdue:

            results.append(
                result
            )

    return results


def calculate_sla_compliance_rate(
    attempts: Iterable[
        RecoveryAttempt
    ],
    *,
    sla: timedelta,
    now: datetime | None = None,
) -> float:
    """
    Calculate the percentage of recovery
    attempts currently complying with SLA.

    Terminal attempts are considered
    compliant.
    """

    attempt_list = list(
        attempts
    )

    if not attempt_list:

        return 1.0

    compliant_count = 0

    for attempt in attempt_list:

        result = evaluate_recovery_sla(
            attempt,
            sla=sla,
            now=now,
        )

        if not result.overdue:

            compliant_count += 1

    return round(
        compliant_count
        / len(attempt_list),
        4,
    )