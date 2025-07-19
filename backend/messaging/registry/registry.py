from typing import Dict, Type 

from messaging.events.base import BaseEvent 


_EVENT_REGISTRY: Dict[str, Type[BaseEvent]] = {}

def register_event(event_cls: Type[BaseEvent]) -> None:
    _EVENT_REGISTRY[event_cls.event_name] = event_cls


def get_event_cls(event_name: str) -> Type[BaseEvent]:
    return _EVENT_REGISTRY[event_name]
