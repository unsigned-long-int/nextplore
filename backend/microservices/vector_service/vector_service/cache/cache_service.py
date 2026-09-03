from uuid import UUID

from nextplore_sdk.cache.client.interface import Cache
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from svc_vector_contracts.models import (
    EmbeddingQuery,
    TableMetadata,
    TableProfile,
    VectorIndexStats,
    VectorMetadata,
    VectorMetadataQuery,
    VectorSearchResult,
)

from vector_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_stats(self, user_identity: UserIdentity) -> VectorIndexStats:
        cache_key = get_string_cache_key(
            value=f"{user_identity.organization_id!s}{user_identity.user_id!s}",
            prefix="stats",
        )
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=VectorIndexStats,
        )

    async def set_stats(
        self, user_identity: UserIdentity, response: VectorIndexStats
    ) -> None:
        cache_key = get_string_cache_key(
            value=f"{user_identity.organization_id!s}{user_identity.user_id!s}",
            prefix="stats",
        )
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
        )

    async def get_vector_metas(
        self, user_identity: UserIdentity, request: VectorMetadataQuery
    ) -> list[VectorMetadata]:
        cache_key = get_cache_key(model=request, prefix="metas")
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=VectorMetadata,
        )

    async def set_vector_metas(
        self,
        user_identity: UserIdentity,
        request: VectorMetadataQuery,
        response: list[VectorMetadata],
    ) -> None:
        cache_key = get_cache_key(model=request, prefix="metas")
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
        )

    async def delete_vector_metas(
        self, user_identity: UserIdentity, request: VectorMetadataQuery
    ) -> None:
        cache_key = get_cache_key(model=request, prefix="metas")
        await self.cache.delete(
            user_identity.organization_id, user_identity.user_id, cache_key
        )

    async def get_qdrant_vectors(
        self, user_identity: UserIdentity, request: EmbeddingQuery
    ) -> list[VectorSearchResult]:
        cache_key = get_cache_key(model=request, prefix="qdrant-vectors")
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=VectorSearchResult,
        )

    async def set_qdrant_vectors(
        self,
        user_identity: UserIdentity,
        request: EmbeddingQuery,
        response: list[VectorSearchResult],
    ) -> None:
        cache_key = get_cache_key(model=request, prefix="qdrant-vectors")
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
        )

    async def get_vector_profiles(
        self, user_identity: UserIdentity, datastore_id: UUID
    ) -> list[TableProfile]:
        cache_key = get_string_cache_key(
            value=f"{user_identity.organization_id!s}{user_identity.user_id!s}{datastore_id!s}",
            prefix="vector-profiles",
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=TableProfile,
        )

    async def set_vector_profiles(
        self,
        user_identity: UserIdentity,
        datastore_id: UUID,
        response: list[TableMetadata],
    ) -> None:
        cache_key = get_string_cache_key(
            value=f"{user_identity.organization_id!s}{user_identity.user_id!s}{datastore_id!s}",
            prefix="vector-profiles",
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
        )
