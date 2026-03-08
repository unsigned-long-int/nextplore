from typing import List

from svc_ai_orm_context_contracts.models import (
    ModelInfo,
    ORMContextRequest,
    ORMContextResponse
)

from llm_inference_service.api.context import UserIdentity
from nextplore_sdk.cache.utils.key_factory import get_string_cache_key, get_cache_key
from nextplore_sdk.cache.client.interface import Cache


class CacheService:
    def __init__(self, cache: Cache) -> None:
        self.cache = cache

    async def get_models(
        self,
        user_identity: UserIdentity,
    ) -> List[ModelInfo]:
        cache_key = get_string_cache_key(value='available-models', prefix='models')
        return await self.cache.get_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=ModelInfo
        )
    
    async def set_models(
        self,
        user_identity: UserIdentity,
        response: List[ModelInfo],
        ttl: int = 600
    ) -> None:
        cache_key = get_string_cache_key(value='available-models', prefix='models')
        await self.cache.set_many(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response,
            ttl=ttl
        )

    async def get_orm_context(
        self, 
        user_identity: UserIdentity,
        request: ORMContextRequest
    ) -> ORMContextResponse:
        
        cache_key = get_cache_key(model=request, prefix='orm-context')
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=ORMContextResponse
        )
    
    async def set_orm_context(
        self, 
        user_identity: UserIdentity,
        request: ORMContextRequest,
        response: ORMContextResponse
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='orm-context')
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )
