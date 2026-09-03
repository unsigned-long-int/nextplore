from typing import ClassVar

from kafka_messaging.events.base import BaseEvent
from pydantic import UUID4, BaseModel


class TableMeta(BaseModel):
    datastore_id: UUID4
    datastore_name: str
    datastore_descr: str
    schema_name: str
    table_name: str
    column_names: list[str]


class DataStoreMetaCrawled(BaseEvent):
    event_name: ClassVar[str] = "datastore.meta.crawled"
    version: ClassVar[str] = "v1"

    table_metas: list[TableMeta]

    def get_topics(self) -> list[str]:
        return [self.event_name]
