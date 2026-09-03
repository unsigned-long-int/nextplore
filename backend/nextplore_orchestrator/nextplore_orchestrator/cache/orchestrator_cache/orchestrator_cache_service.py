
from nextplore_sdk.cache.client.interface import Cache
from nextplore_sdk.cache.utils.key_factory import get_cache_key, get_string_cache_key
from svc_nextplore_orchestrator_contracts.models import RegisterResponse

from nextplore_orchestrator.api.context import UserIdentity
from nextplore_orchestrator.api.models.ai_query_request import AIQueryRequest
from nextplore_orchestrator.api.models.ai_query_response import AIQueryResponse
from nextplore_orchestrator.api.models.user_profile import UserProfile
from nextplore_orchestrator.api.models.user_stats import UserStats


class OrchestratorCacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_user_stats(self, user_identity: UserIdentity) -> UserStats:
        key = f"{user_identity.organization_id}{user_identity.user_id}"
        cache_key = get_string_cache_key(value=key, prefix="user-stats")
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=UserStats,
        )

    async def set_user_stats(
        self,
        user_identity: UserIdentity,
        response: UserStats,
        ttl: int | None = None,
    ) -> None:
        key = f"{user_identity.organization_id}{user_identity.user_id}"
        cache_key = get_string_cache_key(value=key, prefix="user-stats")
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
            ttl=ttl,
        )

    async def delete_user_stats(self, user_identity: UserIdentity) -> None:
        key = f"{user_identity.organization_id}{user_identity.user_id}"
        cache_key = get_string_cache_key(value=key, prefix="user-stats")
        await self.cache.delete(cache_key)

    async def get_user_profile(self, tid: str, oid: str) -> UserProfile:
        key = f"{tid}{oid}"
        cache_key = get_string_cache_key(value=key, prefix="user-profile")
        return await self.cache.get_one(tid, oid, cache_key, model=UserProfile)

    async def set_user_profile(
        self, tid, oid, response: UserProfile, ttl: int | None = None
    ) -> None:
        key = f"{tid}{oid}"
        cache_key = get_string_cache_key(value=key, prefix="user-profile")
        await self.cache.set_one(tid, oid, cache_key, value=response, ttl=ttl)

    async def get_onboarding_response(self, email_domain: str) -> RegisterResponse:
        key = email_domain
        cache_key = get_string_cache_key(value=key, prefix="onboarding-request")
        return await self.cache.get_one(cache_key, model=RegisterResponse)

    async def set_onboarding_response(
        self, response: RegisterResponse, email_domain: str, ttl: int | None = None
    ) -> None:
        key = email_domain
        cache_key = get_string_cache_key(value=key, prefix="onboarding-request")
        await self.cache.set_one(cache_key, value=response, ttl=ttl)

    async def set_ai_query_response(
        self,
        user_identity: UserIdentity,
        request: AIQueryRequest,
        response: AIQueryResponse,
    ) -> None:
        cache_key = get_cache_key(model=request, prefix="ai-query")
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
        )

    async def get_ai_query_response(
        self, user_identity: UserIdentity, request: AIQueryRequest
    ) -> AIQueryResponse:
        cache_key = get_cache_key(model=request, prefix="ai-query")
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=AIQueryResponse,
        )
