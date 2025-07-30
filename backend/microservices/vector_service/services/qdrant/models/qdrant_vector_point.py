from typing import List
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class QdrantVectorPoint:
    id: UUID
    user_id: UUID
    organization_id: UUID
    vector: List[float]
    