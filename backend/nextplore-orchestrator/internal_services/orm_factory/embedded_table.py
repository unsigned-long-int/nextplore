from typing import List
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class EmbeddedTable:
    integration_id: UUID
    schema_name: str
    table_name: str
    embeddings: List[float]
    