import logging
from typing import List

from vector_service.services.vector_store_service.exceptions import (
    DeleteVectorDBFailed,
    SearchVectorDBFailed,
    UpsertVectorDBFailed
)
from vector_service.services.vector_store_service.clients import VectorStoreClient
from vector_service.services.vector_store_service.models import VectorPoint, Vector
from vector_service.api.context import UserIdentity


logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self, client: VectorStoreClient) -> None:
        self.client = client

    async def delete_vectors(
        self, 
        vector_ids: List[str],
        user_id: str,
        organization_id: str
    ) -> None:
        try:
            await self.client.delete_vectors(
                vector_ids,
                user_id,
                organization_id
            )
        except DeleteVectorDBFailed:
            raise
        except Exception as e:
            msg = f'Delete vectors via {self.client.__class__.__name__} failed: {e}'
            logger.error(msg, exc_info=True)
            raise DeleteVectorDBFailed(msg)
        
    async def search_nearest_vectors(
        self,
        user_identity: UserIdentity, 
        embedding: List[float],
        top_k: int = 5
    ) -> List[Vector]:
        try:
            return await self.client.search_nearest_vectors(
                user_identity,
                embedding,
                top_k
            )
        except SearchVectorDBFailed:
            raise
        except Exception as e:
            msg = f'Search vectors via {self.client.__class__.__name__} failed: {e}'
            logger.error(msg, exc_info=True)
            raise SearchVectorDBFailed(msg)

    async def upsert_vectors(
        self,
        vector_points: List[VectorPoint]
    ) -> None:
        try:
            await self.client.upsert_vectors(vector_points)
        except UpsertVectorDBFailed:
            raise
        except Exception as e:
            msg = f'Upsert vectors via {self.client.__class__.__name__} failed: {e}'
            logger.error(msg, exc_info=True)
            raise UpsertVectorDBFailed(msg)
        
    async def aclose(self) -> None:
        try:
            await self.client.aclose()
        except Exception:
            logger.debug('VectorStoreService close ignored', exc_info=True)
