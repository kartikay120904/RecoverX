from dataclasses import dataclass
from typing import Any


@dataclass
class SimulationResult:
    """
    Complete output of a simulation run.

    Contains generated entities, payment lifecycle
    events, recovery attempts, metrics, and
    batch-level incident analysis.
    """

    merchants: list[Any]

    customers: list[Any]

    orders: list[Any]

    payments: list[Any]

    events: list[Any]

    recovery_attempts: list[Any]

    report: Any

    incident_analysis: Any | None = None