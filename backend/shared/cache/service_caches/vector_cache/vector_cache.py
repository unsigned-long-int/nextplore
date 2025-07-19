from shared.cache.utils import get_cache_key
from shared.cache.client import BaseCache
from shared.contracts.vector_service import (
    VectorStatsResponse,
    VectorMetaRequest
)


class VectorServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='vector_service', version='v1')
    
    async def get_vector_stats(self, request: VectorMetaRequest) -> VectorStatsResponse:
        cache_key = get_cache_key(request)
        return await self.get(cache_key, model=VectorStatsResponse)
    
    async def set_vector_stats(
            self, 
            request: VectorMetaRequest, 
            response: VectorStatsResponse
    ) -> None:
        cache_key = get_cache_key(request)
        await self.set(cache_key, value=response)

vector_service_cache = VectorServiceCache()