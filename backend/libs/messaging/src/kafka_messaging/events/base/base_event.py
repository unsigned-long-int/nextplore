from typing import Optional, List, Dict, ClassVar
from uuid import UUID, uuid4
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, timezone


class BaseEvent(BaseModel, ABC):
    event_name: ClassVar[str] 
    version: ClassVar[str] 

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID4
    organization_id: UUID4

    def headers(self) -> Dict[str, str]:
        return {
            'event_name': self.event_name,
            'event_version': str(self.version),
            'event_id': str(self.event_id),
            'organization_id': str(self.organization_id),
            'user_id': str(self.user_id),
            'timestamp': self.timestamp.isoformat(),
        }
    
    @property
    def partition_key(self) -> bytes:
        return str(self.organization_id).encode('utf-8')

    @abstractmethod
    def get_topics(self) -> List[str]:
        raise NotImplementedError
    