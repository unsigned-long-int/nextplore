from typing import Protocol, runtime_checkable, List, Any
from uuid import UUID
from services.vector_store_service.models import VectorPoint

from api.context import UserIdentity


@runtime_checkable
class VectorStoreClient(Protocol):
    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity, 
        embedding: List[float],
        top_k: int = 5
    ) ->  List[UUID]: ...


    async def delete_vectors(
        self,
        vector_ids: List[str],
        user_id: str,
        organization_id: str
    ) -> None: ...


    async def upsert_vectors(
        self,
        vector_points: List[VectorPoint]
    ) -> None: ...


    async def aclose(self) -> None: ...