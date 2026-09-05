from backend.app.domain.enums import RecoveryStatus


class RecoveryStateMachine:
    """
    Defines and validates allowed transitions in the
    recovery lifecycle.

    This class is intentionally independent from the
    existing execution service so that existing recovery
    behavior is not affected.
    """

    _TRANSITIONS: dict[
        RecoveryStatus,
        set[RecoveryStatus],
    ] = {
        RecoveryStatus.PROPOSED: {
            RecoveryStatus.APPROVED,
            RecoveryStatus.REJECTED,
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        },

        RecoveryStatus.APPROVED: {
            RecoveryStatus.SCHEDULED,
            RecoveryStatus.CANCELLED,
        },

        RecoveryStatus.REJECTED: set(),

        RecoveryStatus.SCHEDULED: {
            RecoveryStatus.EXECUTING,
            RecoveryStatus.CANCELLED,
        },

        RecoveryStatus.EXECUTING: {
            RecoveryStatus.SUCCEEDED,
            RecoveryStatus.FAILED,
        },

        RecoveryStatus.SUCCEEDED: set(),

        RecoveryStatus.FAILED: set(),

        RecoveryStatus.CANCELLED: set(),
    }

    @classmethod
    def can_transition(
        cls,
        current_status: RecoveryStatus,
        next_status: RecoveryStatus,
    ) -> bool:
        """
        Return True when the requested lifecycle transition
        is allowed.
        """

        return (
            next_status
            in cls._TRANSITIONS.get(
                current_status,
                set(),
            )
        )

    @classmethod
    def allowed_transitions(
        cls,
        current_status: RecoveryStatus,
    ) -> set[RecoveryStatus]:
        """
        Return all statuses reachable from the current state.
        """

        return set(
            cls._TRANSITIONS.get(
                current_status,
                set(),
            )
        )

    @classmethod
    def is_terminal(
        cls,
        status: RecoveryStatus,
    ) -> bool:
        """
        Return True when the status has no further
        lifecycle transitions.
        """

        return len(
            cls._TRANSITIONS.get(
                status,
                set(),
            )
        ) == 0

    @classmethod
    def validate_transition(
        cls,
        current_status: RecoveryStatus,
        next_status: RecoveryStatus,
    ) -> None:
        """
        Validate a lifecycle transition.

        Raises ValueError when the transition is invalid.
        """

        if not cls.can_transition(
            current_status,
            next_status,
        ):
            raise ValueError(
                "Invalid recovery status transition: "
                f"{current_status.value} -> "
                f"{next_status.value}"
            )