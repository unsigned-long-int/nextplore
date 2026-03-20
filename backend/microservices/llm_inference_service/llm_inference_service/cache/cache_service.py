from typing import List

from svc_llm_inference_contracts.models import (
    ModelInfo,
    ORMContextRequest,
    ORMContextResponse,
    ChatRequest,
    ChatResponse
)
from nextplore_sdk.cache.utils.key_factory import get_string_cache_key, get_cache_key
from nextplore_sdk.cache.client.interface import Cache

from llm_inference_service.api.context import UserIdentity



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

    async def get_chat_response(
        self,
        user_identity: UserIdentity,
        request: ChatRequest
    ) -> ChatResponse:
        cache_key = get_cache_key(model=request, prefix='chat-response')
        return await self.cache.get_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            model=ChatResponse
        )

    async def set_chat_response(
        self,
        user_identity: UserIdentity,
        request: ChatRequest,
        response: ChatResponse,
    ) -> None:
        cache_key = get_cache_key(model=request, prefix='chat-response')
        await self.cache.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )