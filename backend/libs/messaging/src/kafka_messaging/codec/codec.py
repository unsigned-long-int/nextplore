from typing import Any, Protocol, runtime_checkable

from kafka_messaging.events.base import BaseEvent


@runtime_checkable
class Codec(Protocol):
    def serialize(self, topic: str, event: BaseEvent) -> bytes: ...
    def deserialize(self, value: bytes) -> dict[str, Any]: ...
