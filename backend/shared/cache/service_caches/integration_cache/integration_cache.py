from shared.cache.utils import get_cache_key
from shared.cache.client import BaseCache
from shared.contracts.integration_service import (
    FilteredCrawlRequest, 
    CrawlResponse,
    IntegrationStatsRequest,
    IntegrationStatsResponse
)


class IntegrationServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='integration_service', version='v1')

    async def crawl_filtered_integration(self, request: FilteredCrawlRequest) -> CrawlResponse:
        cache_key = get_cache_key(request)
        return await self.get(cache_key, model=CrawlResponse)
    
    async def get_integration_stats(self, request: IntegrationStatsRequest) -> IntegrationStatsResponse:
        cache_key = get_cache_key(request)
        return await self.get(cache_key, model=IntegrationStatsResponse)
    
    async def set_integration_stats(
            self, 
            request: IntegrationStatsRequest, 
            response: IntegrationStatsResponse
    ) -> None:
        cache_key = get_cache_key(request)
        await self.set(cache_key, value=response)

integration_service_cache = IntegrationServiceCache()