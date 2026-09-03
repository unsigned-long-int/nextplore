
from kafka_messaging.events.base import BaseEvent

_EVENT_REGISTRY: dict[str, type[BaseEvent]] = {}


def register_event(event_cls: type[BaseEvent]) -> None:
    _EVENT_REGISTRY[event_cls.event_name] = event_cls


def get_event_cls(event_name: str) -> type[BaseEvent]:
    return _EVENT_REGISTRY[event_name]
