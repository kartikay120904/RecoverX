import pytest

from backend.app.domain.enums import RecoveryStatus
from backend.app.services.recovery_state_machine import (
    RecoveryStateMachine,
)


def test_proposed_can_be_approved():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.PROPOSED,
            RecoveryStatus.APPROVED,
        )
        is True
    )


def test_proposed_can_be_rejected():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.PROPOSED,
            RecoveryStatus.REJECTED,
        )
        is True
    )


def test_proposed_can_be_scheduled():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SCHEDULED,
        )
        is True
    )


def test_approved_can_be_scheduled():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.APPROVED,
            RecoveryStatus.SCHEDULED,
        )
        is True
    )


def test_scheduled_can_execute():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.EXECUTING,
        )
        is True
    )


def test_executing_can_succeed():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.EXECUTING,
            RecoveryStatus.SUCCEEDED,
        )
        is True
    )


def test_executing_can_fail():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.EXECUTING,
            RecoveryStatus.FAILED,
        )
        is True
    )


def test_terminal_status_cannot_transition():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.EXECUTING,
        )
        is False
    )


def test_invalid_transition_returns_false():

    assert (
        RecoveryStateMachine.can_transition(
            RecoveryStatus.PROPOSED,
            RecoveryStatus.SUCCEEDED,
        )
        is False
    )


def test_terminal_status_detection():

    assert (
        RecoveryStateMachine.is_terminal(
            RecoveryStatus.SUCCEEDED,
        )
        is True
    )

    assert (
        RecoveryStateMachine.is_terminal(
            RecoveryStatus.FAILED,
        )
        is True
    )

    assert (
        RecoveryStateMachine.is_terminal(
            RecoveryStatus.CANCELLED,
        )
        is True
    )


def test_non_terminal_status_detection():

    assert (
        RecoveryStateMachine.is_terminal(
            RecoveryStatus.PROPOSED,
        )
        is False
    )

    assert (
        RecoveryStateMachine.is_terminal(
            RecoveryStatus.EXECUTING,
        )
        is False
    )


def test_allowed_transitions():

    transitions = (
        RecoveryStateMachine.allowed_transitions(
            RecoveryStatus.PROPOSED,
        )
    )

    assert (
        RecoveryStatus.APPROVED
        in transitions
    )

    assert (
        RecoveryStatus.REJECTED
        in transitions
    )

    assert (
        RecoveryStatus.SCHEDULED
        in transitions
    )


def test_validate_valid_transition():

    RecoveryStateMachine.validate_transition(
        RecoveryStatus.PROPOSED,
        RecoveryStatus.APPROVED,
    )


def test_validate_invalid_transition():

    with pytest.raises(
        ValueError,
        match="Invalid recovery status transition",
    ):

        RecoveryStateMachine.validate_transition(
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.EXECUTING,
        )