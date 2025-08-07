from typing import List, Optional

from nextplore_shared.cache.utils.key_factory import get_cache_key
from nextplore_shared.cache.client.base_redis_client import BaseCache
from nextplore_shared.contracts.integration_service.filtered_crawl_request import FilteredCrawlRequest
from nextplore_shared.contracts.integration_service.crawl_response import CrawlResponse
from nextplore_shared.contracts.integration_service.integration_stats_request import IntegrationStatsRequest
from nextplore_shared.contracts.integration_service.integration_stats_response import IntegrationStatsResponse
from nextplore_shared.contracts.integration_service.integration_metadata_request import IntegrationMetadataRequest
from nextplore_shared.contracts.integration_service.integration_metadata_response import IntegrationMetadataResponse
from nextplore_shared.contracts.integration_service.prepared_integration_get_request import PreparedIntegrationGetRequest
from nextplore_shared.contracts.integration_service.integration_profile_response import IntegrationProfileResponse
from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity


class IntegrationServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='integration_service', version='v1')

    async def get_filtered_integration(
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

    async def delete_filtered_integration(
        self,
        user_identity: UserIdentity,
        request: FilteredCrawlRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='filtered-crawl')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
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

    async def delete_integration_stats(
        self,
        user_identity: UserIdentity,
        request: IntegrationStatsRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='stats')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
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

    async def delete_integration_metadata(
        self,
        user_identity: UserIdentity,
        request: IntegrationMetadataRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='metas')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
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

    async def delete_integrations(
        self,
        user_identity: UserIdentity,
        request: PreparedIntegrationGetRequest
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='profile')
        await self.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )


integration_service_cache = IntegrationServiceCache()