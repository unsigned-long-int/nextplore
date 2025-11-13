from nextplore_sdk.cache.utils.key_factory import get_cache_key
from nextplore_sdk.cache.client.interface import Cache
from embedding_service.api.models.embedding_response import EmbeddingResponse
from embedding_service.api.models.query_embedding_request import QueryEmbeddingRequest
from embedding_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_embedding(
        self,
        user_identity: UserIdentity,
        request: QueryEmbeddingRequest
    ) -> EmbeddingResponse:
        cache_key = get_cache_key(model=request, prefix='query-embed')
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=EmbeddingResponse
        )
    
    async def set_embedding(
        self,
        user_identity: UserIdentity,
        request: QueryEmbeddingRequest,
        response: EmbeddingResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='query-embed')
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def delete_embedding(
        self,
        user_identity: UserIdentity,
        request: QueryEmbeddingRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='query-embed')
        await self.cache.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )
