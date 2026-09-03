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


class ORMEmbedding(BaseModel):
    datastore_id: UUID4
    schema_name: str
    table_name: str
    table_meta: TableMeta
    embedding: list[float]


class CrawlMetaEmbedded(BaseEvent):
    event_name: ClassVar[str] = "crawlmeta.embedded"
    version: ClassVar[str] = "v1"

    orm_embedding: list[ORMEmbedding]

    def get_topics(self) -> list[str]:
        return [self.event_name]
