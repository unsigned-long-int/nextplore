from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity
from nextplore_shared.cache.utils.key_factory import get_cache_key
from nextplore_shared.cache.client.base_redis_client import BaseCache
from nextplore_shared.contracts.embedding_service.embedding_response import EmbeddingResponse
from nextplore_shared.contracts.embedding_service.query_embedding_request import QueryEmbeddingRequest


class EmbeddingServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='embedding_service', version='v1')

    async def get_embedding(
        self,
        user_identity: UserIdentity,
        request: QueryEmbeddingRequest
    ) -> EmbeddingResponse:
        cache_key = get_cache_key(model=request, prefix='query-embed')
        return await self.get_one(
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
        await self.set_one(
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
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )
    
embedding_service_cache = EmbeddingServiceCache()