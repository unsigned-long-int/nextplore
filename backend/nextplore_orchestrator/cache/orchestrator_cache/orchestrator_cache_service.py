from typing import Optional

from nextplore_sdk.identity_service.identity_model.user_identity import UserIdentity
from nextplore_sdk.cache.utils.key_factory import get_string_cache_key
from nextplore_sdk.cache.client.interface import Cache
from nextplore_sdk.contracts.nextplore_orchestrator_service.user_stats import UserStats
from nextplore_sdk.contracts.nextplore_orchestrator_service.user_profile import UserProfile


class OrchestratorCacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_user_stats(
        self,
        user_identity: UserIdentity
    ) -> UserStats:
        key = f'{user_identity.organization_id}{user_identity.user_id}'
        cache_key = get_string_cache_key(value=key, prefix='user-stats')
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=UserStats
        )
    
    async def set_user_stats(
        self,
        user_identity: UserIdentity,
        response: UserStats,
        ttl: Optional[int] = None
    ) -> None:
        key = f'{user_identity.organization_id}{user_identity.user_id}'
        cache_key = get_string_cache_key(value=key, prefix='user-stats')
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
            ttl=ttl
        )

    async def delete_user_stats(
        self, 
        user_identity: UserIdentity
    ) -> None:
        key = f'{user_identity.organization_id}{user_identity.user_id}'
        cache_key = get_string_cache_key(value=key, prefix='user-stats')
        await self.cache.delete(cache_key)

    async def get_user_profile(
        self,
        tid: str,
        oid: str
    ) -> UserProfile:
        key = f'{tid}{oid}'
        cache_key = get_string_cache_key(value=key, prefix='user-profile')
        return await self.cache.get_one(
            tid,
            oid,
            cache_key,
            model=UserProfile
        )
    
    async def set_user_profile(
        self,
        tid,
        oid,
        response: UserProfile,
        ttl: Optional[int] = None
    ) -> None:
        key = f'{tid}{oid}'
        cache_key = get_string_cache_key(value=key, prefix='user-profile')
        await self.cache.set_one(
            tid,
            oid,
            cache_key,
            value=response,
            ttl=ttl
        )
