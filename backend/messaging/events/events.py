from typing import Optional, List, Dict, ClassVar
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Event(BaseModel, ABC):
    event_name: ClassVar[str] 
    version: ClassVar[str] 

    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))

    @abstractmethod
    def get_topics(self) -> List[str]:
        raise NotImplementedError
    

class IntegrationMetaCrawled(Event):
    event_name: ClassVar[str] = 'integrationmeta.crawled'
    version: ClassVar[str] = 'v1'

    table_metas: List[Dict[str, str]]

    def get_topics(self) -> List[str]:
        return [self.event_name]


class CrawlMetaVectorized(Event):
    event_name: ClassVar[str] = 'crawlmeta.vectorized'
    version: ClassVar[str] = 'v1'

    orm_vectors: List[Dict[str, str]]

    def get_topics(self) -> List[str]:
        return [self.event_name]
