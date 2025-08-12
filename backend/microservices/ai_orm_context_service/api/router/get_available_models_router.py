from fastapi import APIRouter, Depends

from nextplore_sdk.contracts.ai_orm_context_service.avilable_models_response import (
    ModelInfo, 
    AvailableModelsResponse
)
from cache import CacheService, get_cache_service
from services.models_registry import ModelsRegistry, get_models_registry

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])

@router.get('/get-models', response_model=AvailableModelsResponse)
async def get_models(
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service)
) -> AvailableModelsResponse:
    cached = await cache_service.get_models()
    if cached:
        return cached
    
    models = []
    for model in models_registry.list_models():
        models.append(ModelInfo(
            provider=model.get('provider'),
            model_id=model.get('model_id'),
            label=model.get('label'),
            tags=model.get('tags', [])
        ))

    response = AvailableModelsResponse(models=models)
    await cache_service.set_models(response)
    return response
