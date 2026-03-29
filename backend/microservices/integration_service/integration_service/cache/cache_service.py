from typing import List
from uuid import UUID
from svc_integration_contracts.models import (
    FilteredCrawlRequest,
    CrawlResponse,
    DataStoreStatsResponse,
    DataStoreConnectionProfile,
    DataStoreProfile,
    CertProfile,
    UserLlmProfile
)
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from nextplore_sdk.cache.client.interface import Cache

from integration_service.api.context import UserIdentity


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_filtered_datastore(
        self, 
        user_identity: UserIdentity, 
        request: FilteredCrawlRequest
    ) -> CrawlResponse:
        cache_key = get_cache_key(model=request, prefix='datastore-filtered-crawl')
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=CrawlResponse
        )
    
    async def set_filtered_datastore(
        self, 
        user_identity: UserIdentity,
        request: FilteredCrawlRequest, 
        response: CrawlResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='datastore-filtered-crawl')
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )
    
    async def get_datastore_stats(
        self, 
        user_identity: UserIdentity
    ) -> DataStoreStatsResponse:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-stats'
        )
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            model=DataStoreStatsResponse
        )
    
    async def set_datastore_stats(
        self, 
        user_identity: UserIdentity,
        response: DataStoreStatsResponse
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-stats'
        )
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key, 
            value=response
        )

    async def get_datastore_connection_profile(
        self, 
        user_identity: UserIdentity,
        datastore_id: UUID,
    ) -> DataStoreConnectionProfile:
        cache_key = get_string_cache_key(
            value=str(datastore_id),
            prefix='datastore-connection-profile'
        )
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=DataStoreConnectionProfile
        )
    
    async def set_datastore_connection_profile(
        self,
        user_identity: UserIdentity,
        datastore_id: UUID,
        response: DataStoreConnectionProfile
    ) -> None:
        cache_key = get_string_cache_key(
            value=str(datastore_id),
            prefix='datastore-connection-profile'
        )
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def get_datastore_profiles(
        self,
        user_identity: UserIdentity,
    ) -> List[DataStoreProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-profile'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=DataStoreProfile
        )
    
    async def set_datastore_profiles(
        self,
        user_identity: UserIdentity,
        response: List[DataStoreProfile]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-profile'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )

    async def get_datastore_cert_profiles(
        self,
        user_identity: UserIdentity
    ) -> List[CertProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-cert-profile'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=CertProfile
        )

    async def set_datastore_cert_profiles(
        self,
        user_identity: UserIdentity,
        response: List[CertProfile]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-cert-profile'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )


    async def delete_datastore_cert_profiles(
        self,
        user_identity: UserIdentity,
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='datastore-cert-profile'
        )

        await self.cache.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )

    async def delete_user_llm_profiles(
        self,
        user_identity: UserIdentity,
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='user-llm-profile'
        )
        await self.cache.delete(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key
        )

    async def get_user_llm_profiles(
        self,
        user_identity: UserIdentity
    ) -> List[UserLlmProfile]:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='user-llm-profile'
        )
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=CertProfile
        )

    async def set_user_llm_profiles(
        self,
        user_identity: UserIdentity,
        response: List[UserLlmProfile]
    ) -> None:
        cache_key = get_string_cache_key(
            value=f'{str(user_identity.user_id)}{str(user_identity.organization_id)}',
            prefix='user-llm-profile'
        )
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )