from typing import List

from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity
from nextplore_shared.cache.utils.key_factory import get_cache_key
from nextplore_shared.cache.client.base_redis_client import BaseCache
from nextplore_shared.contracts.vector_service.vector_stats_response import VectorStatsResponse
from nextplore_shared.contracts.vector_service.vector_stats_request import VectorStatsRequest
from nextplore_shared.contracts.vector_service.vector_meta_request import VectorMetaRequest
from nextplore_shared.contracts.vector_service.vector_meta_response import VectorMetaResponse
from nextplore_shared.contracts.vector_service.qdrant_vector_request import QDrantVectorRequest
from nextplore_shared.contracts.vector_service.qdrant_vector_response import QDrantVectorResponse
from nextplore_shared.contracts.vector_service.vector_profile_request import VectorProfileRequest
from nextplore_shared.contracts.vector_service.vector_profile_response import VectorProfileResponse


class VectorServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='vector_service', version='v1')
    
    async def get_vector_stats(self, user_identity: UserIdentity, request: VectorStatsRequest) -> VectorStatsResponse:
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
        request: VectorStatsRequest, 
        response: VectorStatsResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='stats')
        await self.set_one(
            user_identity.organization_id, 
            user_identity.user_id, 
            cache_key, 
            value=response
        )

    async def delete_vector_stats(
        self,
        user_identity: UserIdentity,
        request: VectorStatsRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='stats')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
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
    
    async def set_vector_metas(
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

    async def delete_vector_metas(
        self,
        user_identity: UserIdentity,
        request: VectorMetaRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='metas')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )

    async def get_qdrant_vectors(
        self, 
        user_identity: UserIdentity,
        request: QDrantVectorRequest
    ) -> QDrantVectorResponse:
        cache_key = get_cache_key(model=request, prefix='qdrant-vectors')
        return await self.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=QDrantVectorResponse
        )
    
    async def set_qdrant_vectors(
        self, 
        user_identity: UserIdentity,
        request: QDrantVectorRequest,
        response: QDrantVectorResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='qdrant-vectors')
        await self.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def delete_qdrant_vectors(
        self,
        user_identity: UserIdentity,
        request: QDrantVectorRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='qdrant-vectors')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )

    async def get_vector_profiles(
        self, 
        user_identity: UserIdentity,
        request: VectorProfileRequest
    ) -> List[VectorProfileResponse]:
        cache_key = get_cache_key(model=request, prefix='vector-profiles')
        return await self.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=VectorProfileResponse
        )
    
    async def set_vector_profiles(
        self, 
        user_identity: UserIdentity,
        request: VectorProfileRequest,
        response: List[VectorProfileResponse]
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='vector-profiles')
        await self.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def delete_qdrant_vectors(
        self,
        user_identity: UserIdentity,
        request: VectorProfileRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='vector-profiles')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )


vector_service_cache = VectorServiceCache()