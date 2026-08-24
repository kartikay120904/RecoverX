from abc import ABC, abstractmethod
from random import Random

from backend.app.domain.models import Order, Payment


class SimulationScenario(ABC):
    name: str

    @abstractmethod
    def payment_success_rate(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> float:
        """Return the synthetic payment success probability."""

    @abstractmethod
    def applies_to(
        self,
        order: Order,
        payment_method: str,
        timestamp_hour: int,
    ) -> bool:
        """Return whether the scenario affects this payment."""