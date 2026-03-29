from typing import ClassVar, List
from pydantic import UUID4

from kafka_messaging.events.base import BaseEvent


class DataStoreCreated(BaseEvent):
    event_name: ClassVar[str] = 'data_store.created'
    version: ClassVar[str] = 'v1'

    datastore_id: UUID4
    datastore_name: str
    datastore_descr: str

    def get_topics(self) -> List[str]:
        return [self.event_name]
