import pytest

from simulator.batch.recovery_simulation_config import (
    RecoverySimulationConfig,
)


def test_valid_configuration():

    config = (
        RecoverySimulationConfig(
            count=100,
            seed=42,
            scenario_name="baseline",
        )
    )

    assert config.count == 100

    assert config.seed == 42

    assert (
        config.scenario_name
        == "baseline"
    )


def test_default_scenario_name():

    config = (
        RecoverySimulationConfig(
            count=10,
        )
    )

    assert (
        config.scenario_name
        == "default"
    )


def test_negative_count_raises_error():

    with pytest.raises(
        ValueError,
        match="Simulation count cannot be negative",
    ):

        RecoverySimulationConfig(
            count=-1,
        )


def test_empty_scenario_name_raises_error():

    with pytest.raises(
        ValueError,
        match="Scenario name cannot be empty",
    ):

        RecoverySimulationConfig(
            count=10,
            scenario_name="",
        )


def test_whitespace_scenario_name_raises_error():

    with pytest.raises(
        ValueError,
        match="Scenario name cannot be empty",
    ):

        RecoverySimulationConfig(
            count=10,
            scenario_name="   ",
        )