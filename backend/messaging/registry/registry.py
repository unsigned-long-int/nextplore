from typing import Dict, Type 

from messaging.events import events 


_EVENT_REGISTRY: Dict[str, Type[events.Event]] = {}

def register_event(event_cls: Type[events.Event]) -> None:
    _EVENT_REGISTRY[event_cls.event_name] = event_cls


def get_event_cls(event_name: str) -> Type[events.Event]:
    return _EVENT_REGISTRY[event_name]
