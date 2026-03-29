from typing import ClassVar, List
from pydantic import UUID4

from kafka_messaging.events.base import BaseEvent


class DataStoreDeleted(BaseEvent):
    event_name: ClassVar[str] = 'datastore.deleted'
    version: ClassVar[str] = 'v1'

    datastore_id: UUID4

    def get_topics(self) -> List[str]:
        return [self.event_name]
