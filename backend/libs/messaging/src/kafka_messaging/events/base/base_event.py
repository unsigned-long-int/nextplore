from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import ClassVar
from uuid import UUID, uuid4

from pydantic import UUID4, BaseModel, Field


class BaseEvent(BaseModel, ABC):
    event_name: ClassVar[str]
    version: ClassVar[str]

    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime | None = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    user_id: UUID4
    organization_id: UUID4

    def headers(self) -> dict[str, str]:
        return {
            "event_name": self.event_name,
            "event_version": str(self.version),
            "event_id": str(self.event_id),
            "organization_id": str(self.organization_id),
            "user_id": str(self.user_id),
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def partition_key(self) -> bytes:
        return str(self.organization_id).encode("utf-8")

    @abstractmethod
    def get_topics(self) -> list[str]:
        raise NotImplementedError
