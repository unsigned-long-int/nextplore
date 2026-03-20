import asyncio
from typing import List

from nextplore_orchestrator.clients.embedding import EmbeddingClient
from nextplore_orchestrator.clients.vector import VectorClient
from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.domain.models import VectorNeighbourCollection
from nextplore_orchestrator.domain.mappers import vector_neighbours_from_dto
from svc_vector_contracts.models import VectorMetadataQuery, EmbeddingQuery


class VectorSearcher:
    def __init__(
            self,
            embedding_client: EmbeddingClient,
            vector_client: VectorClient,
    ) -> None:
        self.embedding_client = embedding_client
        self.vector_client = vector_client

    async def search(self, query: str, user_identity: UserIdentity) -> VectorNeighbourCollection:
        embedding = await self.embedding_client.embed(query)
        vector_hits = await self.vector_client.get_nearest_neighbours(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=EmbeddingQuery(embedding=embedding.embedding),
        )
        meta = await self.vector_client.get_meta(
            organization_id=user_identity.organization_id,
            user_id=user_identity.user_id,
            payload=VectorMetadataQuery(vector_ids=[h.vector_id for h in vector_hits]),
        )
        return VectorNeighbourCollection(
            query=query,
            vector_neighbours=vector_neighbours_from_dto(meta, vector_hits),
        )

    async def search_many(self, queries: List[str], user_identity: UserIdentity) -> List[VectorNeighbourCollection]:
        return list(await asyncio.gather(*(self.search(q, user_identity) for q in queries)))
