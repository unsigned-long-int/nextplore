from typing import ClassVar, List
from pydantic import UUID4

from kafka_messaging.events.base import BaseEvent


class IntegrationDeleted(BaseEvent):
    event_name: ClassVar[str] = 'integration.deleted'
    version: ClassVar[str] = 'v1'

    integration_id: UUID4

    def get_topics(self) -> List[str]:
        return [self.event_name]
