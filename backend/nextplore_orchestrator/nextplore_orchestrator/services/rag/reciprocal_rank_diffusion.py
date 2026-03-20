from collections import defaultdict
from typing import List, Dict
from uuid import UUID

from nextplore_orchestrator.domain.models import VectorNeighbourCollection, VectorNeighbour, RankedVector

def reciprocal_rank_fusion(vector_collections: List[VectorNeighbourCollection], k: int = 60) -> List[RankedVector]:
    scores: Dict[UUID, float] = defaultdict(float)
    store: Dict[UUID, VectorNeighbour] = {}
    source_queries: Dict[UUID, List[str]] = defaultdict(list)


    for collection in vector_collections:
        sorted_neighbours = sorted(
            collection.vector_neighbours,
            key=lambda v: v.score,
            reverse=True,
        )
        for rank, vector in enumerate(sorted_neighbours):
            scores[vector.id] += 1.0 / (k + rank + 1)
            store[vector.id] = vector
            source_queries[vector.id].append(collection.query)

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [
        RankedVector(
            vector=store[vid],
            rrf_score=score,
            rank=i,
            source_queries=source_queries[vid]
        )
        for i, (vid, score) in enumerate(ranked)
    ]