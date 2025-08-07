from nextplore_shared.contracts.ai_orm_context_service.avilable_models_response import AvailableModelsResponse
from nextplore_shared.cache.utils.key_factory import get_string_cache_key
from nextplore_shared.cache.client.base_redis_client import BaseCache


class AIORMContextServiceCache(BaseCache):
    def __init__(self) -> None:
        super().__init__(namespace='ai_orm_context_cache_service', version='v1')

    async def get_models(self) -> AvailableModelsResponse:
        cache_key = get_string_cache_key(value='available_models', prefix='models')
        return await self.get_one(
            cache_key,
            model=AvailableModelsResponse
        )
    
    async def set_models(
        self, 
        response: AvailableModelsResponse,
        ttl: int = 600
    ) -> None:
        cache_key = get_string_cache_key(value='available_models', prefix='models')
        await self.set_one(
            cache_key,
            value=response,
            ttl=ttl
        )
    
ai_orm_context_service_cache = AIORMContextServiceCache()