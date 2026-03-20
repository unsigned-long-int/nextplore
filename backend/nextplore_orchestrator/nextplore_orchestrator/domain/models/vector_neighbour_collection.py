from dataclasses import dataclass
from typing import List
from uuid import UUID


@dataclass(frozen=True)
class OrmMetadata:
    integration_id: UUID
    schema_name: str
    table_name: str
    column_names: List[str]


@dataclass(frozen=True)
class VectorNeighbour:
    id: UUID
    score: float
    orm_metadata: OrmMetadata

    @property
    def snippet(self) -> str:
        return ','.join(self.orm_metadata.column_names)


    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, VectorNeighbour):
            return NotImplemented
        return self.id == other.id


@dataclass(frozen=True)
class VectorNeighbourCollection:
    query: str
    vector_neighbours: List[VectorNeighbour]


@dataclass(frozen=True)
class RankedVector:
    vector: VectorNeighbour
    rrf_score: float
    rank: int
    source_queries: List[str]