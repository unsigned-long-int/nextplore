from collections import defaultdict
from uuid import UUID

from nextplore_orchestrator.domain.models import (
    RankedVector,
    VectorNeighbour,
    VectorNeighbourCollection,
)


def reciprocal_rank_fusion(
    vector_collections: list[VectorNeighbourCollection], k: int = 60
) -> list[RankedVector]:
    scores: dict[UUID, float] = defaultdict(float)
    store: dict[UUID, VectorNeighbour] = {}
    source_queries: dict[UUID, list[str]] = defaultdict(list)

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
            source_queries=source_queries[vid],
        )
        for i, (vid, score) in enumerate(ranked)
    ]
