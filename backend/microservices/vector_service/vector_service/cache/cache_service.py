from typing import List
from uuid import UUID

from svc_vector_contracts.models import (
    EmbeddingQuery,
    VectorSearchResult,
    VectorMetadataQuery,
    TableProfile,
    VectorIndexStats,
    TableMetadata,
    VectorMetadata
)
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from nextplore_sdk.cache.client.interface import Cache

from vector_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache
    
    async def get_stats(self, user_identity: UserIdentity) -> VectorIndexStats:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}',
            prefix='stats'
        )
        return await self.cache.get_one(
            user_identity.organization_id, 
            user_identity.user_id, 
            cache_key, 
            model=VectorIndexStats
        )
    
    async def set_stats(
        self, 
        user_identity: UserIdentity,
        response: VectorIndexStats
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
        request: VectorMetadataQuery
    ) -> List[VectorMetadata]:
        cache_key = get_cache_key(model=request, prefix='metas')
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=VectorMetadata
        )
    
    async def set_vector_metas(
        self, 
        user_identity: UserIdentity,
        request: VectorMetadataQuery,
        response: List[VectorMetadata]
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
        request: VectorMetadataQuery
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
        request: EmbeddingQuery
    ) -> List[VectorSearchResult]:
        cache_key = get_cache_key(model=request, prefix='qdrant-vectors')
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=VectorSearchResult
        )
    
    async def set_qdrant_vectors(
        self, 
        user_identity: UserIdentity,
        request: EmbeddingQuery,
        response: List[VectorSearchResult]
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='qdrant-vectors')
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def get_vector_profiles(
        self, 
        user_identity: UserIdentity,
        datastore_id: UUID
    ) -> List[TableProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}{str(datastore_id)}',
            prefix='vector-profiles'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=TableProfile
        )
    
    async def set_vector_profiles(
        self, 
        user_identity: UserIdentity,
        datastore_id: UUID,
        response: List[TableMetadata]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.organization_id)}{str(user_identity.user_id)}{str(datastore_id)}',
            prefix='vector-profiles'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

