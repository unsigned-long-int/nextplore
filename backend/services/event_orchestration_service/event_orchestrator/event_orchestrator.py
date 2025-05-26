from dataclasses import dataclass, field
from typing import List, Generator

from services.event_orchestration_service.events import events


@dataclass
class EventOrchestrator:
    queue: List[events.Event] = field(
        default_factory=list, init=False, repr=False)

    def collect_new_events(self) -> Generator[events.Event, None, None]:
        while self.queue:
            yield self.queue.pop(0)
