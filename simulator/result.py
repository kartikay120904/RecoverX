from dataclasses import dataclass
from typing import TYPE_CHECKING

from backend.app.domain.events import DomainEvent
from backend.app.domain.models import (
    Customer,
    Merchant,
    Order,
    Payment,
    RecoveryAttempt,
)

if TYPE_CHECKING:
    from simulator.analytics.report import SimulationReport


@dataclass(frozen=True)
class SimulationResult:
    merchants: list[Merchant]
    customers: list[Customer]
    orders: list[Order]
    payments: list[Payment]
    events: list[DomainEvent]
    recovery_attempts: list[RecoveryAttempt]
    report: "SimulationReport | None" = None