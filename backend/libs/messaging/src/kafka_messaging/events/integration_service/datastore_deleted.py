from typing import ClassVar

from kafka_messaging.events.base import BaseEvent
from pydantic import UUID4


class DataStoreDeleted(BaseEvent):
    event_name: ClassVar[str] = "datastore.deleted"
    version: ClassVar[str] = "v1"

    datastore_id: UUID4

    def get_topics(self) -> list[str]:
        return [self.event_name]
