from typing import List
from shared.identity_service.user_identity import UserIdentity
from shared.cache.utils import get_cache_key
from shared.cache.client import BaseCache
from shared.contracts.vector_service import (
    VectorStatsResponse,
    VectorMetaRequest,
    VectorMetaResponse
)


class VectorServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='vector_service', version='v1')
    
    async def get_vector_stats(self, user_identity: UserIdentity, request: VectorMetaRequest) -> VectorStatsResponse:
        cache_key = get_cache_key(model=request, prefix='stats')
        return await self.get_one(
            user_identity.organization_id, 
            user_identity.user_id, 
            cache_key, 
            model=VectorStatsResponse
        )
    
    async def set_vector_stats(
            self, 
            user_identity: UserIdentity,
            request: VectorMetaRequest, 
            response: VectorStatsResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='stats')
        await self.set_one(
            user_identity.organization_id, 
            user_identity.user_id, 
            cache_key, 
            value=response
        )

    async def get_vector_metas(
            self, 
            user_identity: UserIdentity,
            request: VectorMetaRequest
    ) -> List[VectorMetaResponse]:
        cache_key = get_cache_key(model=request, prefix='metas')
        return await self.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=VectorMetaResponse
        )
    
    async def set_vectors_meta(
            self, 
            user_identity: UserIdentity,
            request: VectorMetaRequest,
            response: List[VectorMetaResponse]
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='metas')
        await self.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

vector_service_cache = VectorServiceCache()