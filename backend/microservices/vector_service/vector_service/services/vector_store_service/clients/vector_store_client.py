from typing import Protocol, runtime_checkable

from qdrant_client.http.models import FieldCondition, QueryResponse

from vector_service.api.context import UserIdentity
from vector_service.services.vector_store_service.models import VectorPoint


@runtime_checkable
class VectorStoreClient(Protocol):
    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity,
        embedding: list[float],
        collection: str,
        top_k: int = 5,
        refine_filters: list[FieldCondition] | None = None,
        score_threshold: float | None = None,
    ) -> QueryResponse: ...

    async def delete_vectors(
        self,
        vector_ids: list[str],
        user_id: str,
        organization_id: str,
        collection: str,
    ) -> None: ...

    async def upsert_vectors(
        self,
        vector_points: list[VectorPoint],
        collection: str,
    ) -> None: ...

    async def aclose(self) -> None: ...
