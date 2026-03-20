from typing import Protocol, runtime_checkable, List

from vector_service.services.vector_store_service.models import VectorPoint, Vector
from vector_service.api.context import UserIdentity


@runtime_checkable
class VectorStoreClient(Protocol):
    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity, 
        embedding: List[float],
        top_k: int = 5
    ) ->  List[Vector]: ...


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