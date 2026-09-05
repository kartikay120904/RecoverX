from dataclasses import dataclass


@dataclass(frozen=True)
class RecoverySimulationConfig:
    """
    Immutable configuration for a RecoverX
    batch simulation.

    This configuration controls simulation-level
    behavior only.

    It does not modify recovery, orchestration,
    escalation, or execution logic.
    """

    count: int

    seed: int | None = None

    scenario_name: str = "default"

    def __post_init__(self) -> None:
        """
        Validate simulation configuration.
        """

        if self.count < 0:
            raise ValueError(
                "Simulation count cannot be negative."
            )

        if not self.scenario_name.strip():
            raise ValueError(
                "Scenario name cannot be empty."
            )