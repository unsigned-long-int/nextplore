from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class VectorPoint:
    id: UUID
    user_id: UUID
    organization_id: UUID
    vector: list[float]
    extra: dict[str, Any] = field(default_factory=dict)
