from dataclasses import dataclass
from typing import List

from .vector_neighbour_collection import VectorNeighbourCollection, RankedVector
from .rag_context import RagContext

@dataclass
class RagPipelineResult:
    sub_queries: List[str]
    neighbour_collections: List[VectorNeighbourCollection]
    ranked: List[RankedVector]
    rag_context: RagContext