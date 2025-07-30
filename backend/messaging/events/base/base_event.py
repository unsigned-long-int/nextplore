from typing import Optional, List, ClassVar
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, timezone


class BaseEvent(BaseModel, ABC):
    event_name: ClassVar[str] 
    version: ClassVar[str] 

    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: UUID4
    organization_id: UUID4

    @abstractmethod
    def get_topics(self) -> List[str]:
        raise NotImplementedError
    