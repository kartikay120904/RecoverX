from enum import Enum


class RecoveryScenario(str, Enum):
    """
    Named simulation scenarios supported by
    the RecoverX batch simulator.

    These scenarios currently describe simulation
    intent only.

    They do not modify recovery or escalation
    business logic.
    """

    BASELINE = "baseline"

    HIGH_VALUE = "high_value"

    APPROVAL_HEAVY = "approval_heavy"

    FAILURE_HEAVY = "failure_heavy"

    RETRY_PRESSURE = "retry_pressure"