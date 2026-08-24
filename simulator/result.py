from dataclasses import dataclass

from backend.app.domain.models import (
    Customer,
    Merchant,
    Order,
    Payment,
)
from backend.app.domain.events import DomainEvent


@dataclass(frozen=True)
class SimulationResult:
    merchants: list[Merchant]
    customers: list[Customer]
    orders: list[Order]
    payments: list[Payment]
    events: list[DomainEvent]