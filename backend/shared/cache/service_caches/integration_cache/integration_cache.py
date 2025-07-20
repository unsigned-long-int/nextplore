from typing import List

from shared.cache.utils import get_cache_key
from shared.cache.client import BaseCache
from shared.contracts.integration_service import (
    FilteredCrawlRequest, 
    CrawlResponse,
    IntegrationStatsRequest,
    IntegrationStatsResponse,
    IntegrationMetadataRequest,
    IntegrationMetadataResponse,
    PreparedIntegrationGetRequest,
    IntegrationProfileResponse
)
from shared.identity_service.user_identity import UserIdentity


class IntegrationServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='integration_service', version='v1')

    async def crawl_filtered_integration(
            self, 
            user_identity: UserIdentity, 
            request: FilteredCrawlRequest
        ) -> CrawlResponse:
        cache_key = get_cache_key(model=request, prefix='filtered-crawl')
        return await self.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=CrawlResponse
        )
    
    async def set_filtered_integration(
            self, 
            user_identity: UserIdentity,
            request: FilteredCrawlRequest, 
            response: CrawlResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='filtered-crawl')
        await self.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    
    async def get_integration_stats(
            self, 
            user_identity: UserIdentity, 
            request: IntegrationStatsRequest
        ) -> IntegrationStatsResponse:
        cache_key = get_cache_key(model=request, prefix='stats')
        return await self.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=IntegrationStatsResponse
        )
    
    async def set_integration_stats(
            self, 
            user_identity: UserIdentity,
            request: IntegrationStatsRequest, 
            response: IntegrationStatsResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='stats')
        await self.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def get_integration_metadata(
        self, 
        user_identity: UserIdentity,
        request: IntegrationMetadataRequest
    ) -> IntegrationMetadataResponse:
        cache_key = get_cache_key(model=request, prefix='metas')
        return await self.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=IntegrationMetadataResponse
        )
    
    async def set_integration_metadata(
        self,
        user_identity: UserIdentity,
        request: IntegrationMetadataRequest,
        response: IntegrationMetadataResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='metas')
        await self.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def get_integrations(
        self,
        user_identity: UserIdentity,
        request: PreparedIntegrationGetRequest
    ) -> List[IntegrationProfileResponse]:
        cache_key = get_cache_key(model=request, prefix='profile')
        return await self.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=IntegrationProfileResponse
        )
    
    async def set_integrations(
        self,
        user_identity: UserIdentity,
        request: PreparedIntegrationGetRequest,
        response: List[IntegrationProfileResponse]
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='profile')
        await self.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )
        

    

integration_service_cache = IntegrationServiceCache()