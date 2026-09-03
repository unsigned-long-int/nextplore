from dataclasses import dataclass

from .rag_context import RagContext
from .vector_neighbour_collection import RankedVector, VectorNeighbourCollection


@dataclass
class RagPipelineResult:
    sub_queries: list[str]
    neighbour_collections: list[VectorNeighbourCollection]
    ranked: list[RankedVector]
    rag_context: RagContext
