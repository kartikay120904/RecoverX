from simulator.batch.recovery_scenario import (
    RecoveryScenario,
)

from simulator.batch.recovery_scenario_factory import (
    RecoveryScenarioFactory,
)


def test_create_baseline_scenario():

    config = (
        RecoveryScenarioFactory.baseline(
            count=100,
            seed=42,
        )
    )

    assert config.count == 100

    assert config.seed == 42

    assert (
        config.scenario_name
        == RecoveryScenario.BASELINE.value
    )


def test_create_high_value_scenario():

    config = (
        RecoveryScenarioFactory.high_value(
            count=100,
            seed=42,
        )
    )

    assert (
        config.scenario_name
        == RecoveryScenario.HIGH_VALUE.value
    )


def test_create_approval_heavy_scenario():

    config = (
        RecoveryScenarioFactory.approval_heavy(
            count=100,
            seed=42,
        )
    )

    assert (
        config.scenario_name
        == RecoveryScenario.APPROVAL_HEAVY.value
    )


def test_create_failure_heavy_scenario():

    config = (
        RecoveryScenarioFactory.failure_heavy(
            count=100,
            seed=42,
        )
    )

    assert (
        config.scenario_name
        == RecoveryScenario.FAILURE_HEAVY.value
    )


def test_create_retry_pressure_scenario():

    config = (
        RecoveryScenarioFactory.retry_pressure(
            count=100,
            seed=42,
        )
    )

    assert (
        config.scenario_name
        == RecoveryScenario.RETRY_PRESSURE.value
    )


def test_generic_factory_creation():

    config = (
        RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.HIGH_VALUE,
            count=50,
            seed=99,
        )
    )

    assert config.count == 50

    assert config.seed == 99

    assert (
        config.scenario_name
        == "high_value"
    )