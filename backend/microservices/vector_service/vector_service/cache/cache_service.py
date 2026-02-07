from typing import List
from uuid import UUID

from svc_vector_contracts.models import (
    VectorProfileResponse,
    VectorStatsResponse,
    VectorMetaRequest,
    VectorMetaResponse,
    QDrantVectorRequest,
    QDrantVectorResponse
)
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from nextplore_sdk.cache.client.interface import Cache

from vector_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache
    
    async def get_stats(self, user_identity: UserIdentity) -> VectorStatsResponse:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}',
            prefix='stats'
        )
        return await self.cache.get_one(
            user_identity.organization_id, 
            user_identity.user_id, 
            cache_key, 
            model=VectorStatsResponse
        )
    
    async def set_stats(
        self, 
        user_identity: UserIdentity,
        response: VectorStatsResponse
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}',
            prefix='stats'
        )
        await self.cache.set_one(
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
        return await self.cache.get_many(
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
        await self.cache.set_many(
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
        await self.cache.delete(
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
        return await self.cache.get_one(
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
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def get_vector_profiles(
        self, 
        user_identity: UserIdentity,
        integration_id: UUID
    ) -> List[VectorProfileResponse]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}{str(integration_id)}',
            prefix='vector-profiles'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=VectorProfileResponse
        )
    
    async def set_vector_profiles(
        self, 
        user_identity: UserIdentity,
        integration_id: UUID,
        response: List[VectorProfileResponse]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}{str(integration_id)}',
            prefix='vector-profiles'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

