from backend.app.domain.events import DomainEvent


class EventStream:
    def __init__(self) -> None:
        self._events: list[DomainEvent] = []

    def append(self, event: DomainEvent) -> None:
        self._events.append(event)

    def all(self) -> list[DomainEvent]:
        return self._events.copy()

    def count(self) -> int:
        return len(self._events)