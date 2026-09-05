import pytest

from backend.app.domain.enums import (
    RecoveryStatus,
)
from backend.app.services.recovery_lifecycle import (
    RecoveryLifecycleValidator,
)


@pytest.fixture
def validator():
    return RecoveryLifecycleValidator()


@pytest.mark.parametrize(
    (
        "current_status",
        "next_status",
    ),
    [
        (
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SCHEDULED,
        ),
        (
            RecoveryStatus.PROPOSED,
            RecoveryStatus.CANCELLED,
        ),
        (
            RecoveryStatus.APPROVED,
            RecoveryStatus.SCHEDULED,
        ),
        (
            RecoveryStatus.APPROVED,
            RecoveryStatus.CANCELLED,
        ),
        (
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.EXECUTING,
        ),
        (
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        ),
        (
            RecoveryStatus.EXECUTING,
            RecoveryStatus.SUCCEEDED,
        ),
        (
            RecoveryStatus.EXECUTING,
            RecoveryStatus.FAILED,
        ),
    ],
)
def test_valid_transitions(
    validator,
    current_status,
    next_status,
):
    assert (
        validator.can_transition(
            current_status,
            next_status,
        )
        is True
    )


@pytest.mark.parametrize(
    (
        "current_status",
        "next_status",
    ),
    [
        (
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SUCCEEDED,
        ),
        (
            RecoveryStatus.PROPOSED,
            RecoveryStatus.EXECUTING,
        ),
        (
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.SUCCEEDED,
        ),
        (
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.PROPOSED,
        ),
        (
            RecoveryStatus.FAILED,
            RecoveryStatus.SCHEDULED,
        ),
        (
            RecoveryStatus.CANCELLED,
            RecoveryStatus.EXECUTING,
        ),
        (
            RecoveryStatus.REJECTED,
            RecoveryStatus.SCHEDULED,
        ),
    ],
)
def test_invalid_transitions(
    validator,
    current_status,
    next_status,
):
    assert (
        validator.can_transition(
            current_status,
            next_status,
        )
        is False
    )


def test_validate_transition_does_not_raise_for_valid_transition(
    validator,
):
    validator.validate_transition(
        RecoveryStatus.PROPOSED,
        RecoveryStatus.SCHEDULED,
    )


def test_validate_transition_raises_for_invalid_transition(
    validator,
):
    with pytest.raises(
        ValueError,
        match="Invalid recovery lifecycle transition",
    ):
        validator.validate_transition(
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SUCCEEDED,
        )


def test_allowed_next_statuses_returns_valid_statuses(
    validator,
):
    statuses = validator.allowed_next_statuses(
        RecoveryStatus.PROPOSED,
    )

    assert statuses == {
        RecoveryStatus.SCHEDULED,
        RecoveryStatus.CANCELLED,
    }


def test_allowed_next_statuses_returns_copy(
    validator,
):
    statuses = validator.allowed_next_statuses(
        RecoveryStatus.PROPOSED,
    )

    statuses.add(
        RecoveryStatus.SUCCEEDED,
    )

    original_statuses = (
        validator.allowed_next_statuses(
            RecoveryStatus.PROPOSED,
        )
    )

    assert (
        RecoveryStatus.SUCCEEDED
        not in original_statuses
    )


def test_terminal_statuses_have_no_next_states(
    validator,
):
    terminal_statuses = [
        RecoveryStatus.SUCCEEDED,
        RecoveryStatus.FAILED,
        RecoveryStatus.CANCELLED,
        RecoveryStatus.REJECTED,
    ]

    for status in terminal_statuses:

        assert (
            validator.allowed_next_statuses(
                status,
            )
            == set()
        )