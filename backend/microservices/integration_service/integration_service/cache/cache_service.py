from typing import List
from uuid import UUID
from svc_integration_contracts.models import (
    FilteredCrawlRequest,
    CrawlResponse,
    IntegrationStatsResponse,
    IntegrationConnectionProfile,
    IntegrationProfile,
    CertProfile
)
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from nextplore_sdk.cache.client.interface import Cache

from integration_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_filtered_integration(
        self, 
        user_identity: UserIdentity, 
        request: FilteredCrawlRequest
    ) -> CrawlResponse:
        cache_key = get_cache_key(model=request, prefix='filtered-crawl')
        return await self.cache.get_one(
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
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )
    
    async def get_stats(
        self, 
        user_identity: UserIdentity
    ) -> IntegrationStatsResponse:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='stats'
        )
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=IntegrationStatsResponse
        )
    
    async def set_stats(
        self, 
        user_identity: UserIdentity,
        response: IntegrationStatsResponse
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='stats'
        )
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def get_connection_profile(
        self, 
        user_identity: UserIdentity,
        integration_id: UUID,
    ) -> IntegrationConnectionProfile:
        cache_key = get_string_cache_key(
            value=str(integration_id),
            prefix='connection-profile'
        )
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=IntegrationConnectionProfile
        )
    
    async def set_connection_profile(
        self,
        user_identity: UserIdentity,
        integration_id: UUID,
        response: IntegrationConnectionProfile
    ) -> None:
        cache_key = get_string_cache_key(
            value=str(integration_id),
            prefix='connection-profile'
        )
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def get_profiles(
        self,
        user_identity: UserIdentity,
    ) -> List[IntegrationProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='profile'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=IntegrationProfile
        )
    
    async def set_profiles(
        self,
        user_identity: UserIdentity,
        response: List[IntegrationProfile]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='profile'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def get_cert_profiles(
        self,
        user_identity: UserIdentity
    ) -> List[CertProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='cert-profile'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=CertProfile
        )

    async def set_cert_profiles(
        self,
        user_identity: UserIdentity,
        response: List[CertProfile]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='cert-profile'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )


    async def delete_cert_profiles(
        self,
        user_identity: UserIdentity,
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='cert-profile'
        )

        await self.cache.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )