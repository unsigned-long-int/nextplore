from typing import ClassVar, List
from pydantic import BaseModel, UUID4

from kafka_messaging.events.base import BaseEvent


class TableMeta(BaseModel):
    integration_id: UUID4
    schema_name: str
    table_name: str
    column_names: List[str]


class IntegrationMetaCrawled(BaseEvent):
    event_name: ClassVar[str] = 'integrationmeta.crawled'
    version: ClassVar[str] = 'v1'

    table_metas: List[TableMeta]

    def get_topics(self) -> List[str]:
        return [self.event_name]