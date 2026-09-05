from simulator.batch.recovery_scenario import (
    RecoveryScenario,
)


def test_recovery_scenario_values():

    assert (
        RecoveryScenario.BASELINE.value
        == "baseline"
    )

    assert (
        RecoveryScenario.HIGH_VALUE.value
        == "high_value"
    )

    assert (
        RecoveryScenario.APPROVAL_HEAVY.value
        == "approval_heavy"
    )

    assert (
        RecoveryScenario.FAILURE_HEAVY.value
        == "failure_heavy"
    )

    assert (
        RecoveryScenario.RETRY_PRESSURE.value
        == "retry_pressure"
    )