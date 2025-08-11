from nextplore_shared.contracts.ai_orm_context_service.avilable_models_response import AvailableModelsResponse
from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest
from nextplore_shared.contracts.ai_orm_context_service.orm_context_response import ORMContextResponse
from nextplore_shared.cache.utils.key_factory import get_string_cache_key, get_cache_key
from nextplore_shared.identity_service.identity_model.user_identity import UserIdentity
from nextplore_shared.cache.client.base_redis_client import BaseCache


class AIORMContextServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='ai_orm_context_cache_service', version='v1')

    async def get_models(self) -> AvailableModelsResponse:
        cache_key = get_string_cache_key(value='available-models', prefix='models')
        return await self.get_one(
            cache_key,
            model=AvailableModelsResponse
        )
    
    async def set_models(
        self, 
        response: AvailableModelsResponse,
        ttl: int = 600
    ) -> None:
        cache_key = get_string_cache_key(value='available-models', prefix='models')
        await self.set_one(
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
        return await self.get_one(
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
        await self.set_one(
            user_identity.organization_id,
            user_identity.user_id,
            cache_key,
            value=response
        )
        
    
ai_orm_context_service_cache = AIORMContextServiceCache()