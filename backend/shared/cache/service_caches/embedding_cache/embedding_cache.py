from shared.identity_service.user_identity import UserIdentity
from shared.cache.utils import get_cache_key
from shared.cache.client import BaseCache
from shared.contracts.embedding_service import (
    EmbeddingResponse,
    QueryEmbeddingRequest
)


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
    
embedding_service_cache = EmbeddingServiceCache()