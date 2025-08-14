from typing import Protocol, runtime_checkable, Dict, Any
from messaging.events.base import BaseEvent


@runtime_checkable
class Codec(Protocol):
    def serialize(self, topic: str, event: BaseEvent) -> bytes: ...
    def deserialize(self, value: bytes) -> Dict[str, Any]: ...
