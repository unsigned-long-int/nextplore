from typing import ClassVar, List
from pydantic import BaseModel, UUID4

from kafka_messaging.events.base import BaseEvent


class TableMeta(BaseModel):
    datastore_id: UUID4
    datastore_name: str
    datastore_descr: str
    schema_name: str
    table_name: str
    column_names: List[str]


class ORMEmbedding(BaseModel):
    datastore_id: UUID4
    schema_name: str
    table_name: str
    table_meta: TableMeta
    embedding: List[float]


class CrawlMetaEmbedded(BaseEvent):
    event_name: ClassVar[str] = 'crawlmeta.embedded'
    version: ClassVar[str] = 'v1'

    orm_embedding: List[ORMEmbedding]

    def get_topics(self) -> List[str]:
        return [self.event_name]