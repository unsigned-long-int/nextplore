from typing import ClassVar

from kafka_messaging.events.base import BaseEvent
from pydantic import UUID4


class DataStoreCreated(BaseEvent):
    event_name: ClassVar[str] = "datastore.created"
    version: ClassVar[str] = "v1"

    datastore_id: UUID4
    datastore_name: str
    datastore_descr: str

    def get_topics(self) -> list[str]:
        return [self.event_name]
