from simulator.batch.recovery_scenario import (
    RecoveryScenario,
)

from simulator.batch.recovery_simulation_config import (
    RecoverySimulationConfig,
)


class RecoveryScenarioFactory:
    """
    Creates validated simulation configurations
    for named RecoverX scenarios.

    The factory only constructs simulation
    configuration.

    It does not modify recovery, escalation,
    orchestration, or execution behavior.
    """

    @staticmethod
    def create(
        *,
        scenario: RecoveryScenario,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create a simulation configuration for
        the requested scenario.
        """

        return RecoverySimulationConfig(
            count=count,
            seed=seed,
            scenario_name=scenario.value,
        )

    @staticmethod
    def baseline(
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create a baseline simulation configuration.
        """

        return RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.BASELINE,
            count=count,
            seed=seed,
        )

    @staticmethod
    def high_value(
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create a high-value simulation configuration.
        """

        return RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.HIGH_VALUE,
            count=count,
            seed=seed,
        )

    @staticmethod
    def approval_heavy(
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create an approval-heavy simulation configuration.
        """

        return RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.APPROVAL_HEAVY,
            count=count,
            seed=seed,
        )

    @staticmethod
    def failure_heavy(
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create a failure-heavy simulation configuration.
        """

        return RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.FAILURE_HEAVY,
            count=count,
            seed=seed,
        )

    @staticmethod
    def retry_pressure(
        *,
        count: int,
        seed: int | None = None,
    ) -> RecoverySimulationConfig:
        """
        Create a retry-pressure simulation configuration.
        """

        return RecoveryScenarioFactory.create(
            scenario=RecoveryScenario.RETRY_PRESSURE,
            count=count,
            seed=seed,
        )