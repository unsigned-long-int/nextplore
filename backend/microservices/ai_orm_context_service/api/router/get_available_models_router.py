from fastapi import APIRouter, Depends

from nextplore_shared.contracts.ai_orm_context_service.avilable_models_response import (
    ModelInfo, 
    AvailableModelsResponse
)
from nextplore_shared.cache.service_caches.ai_orm_context_cache.cache import ai_orm_context_service_cache
from services.models_registry import ModelsRegistry, get_models_registry

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])

@router.get('/get-models', response_model=AvailableModelsResponse)
async def get_models(models_registry: ModelsRegistry = Depends(get_models_registry)) -> AvailableModelsResponse:
    cached = await ai_orm_context_service_cache.get_models()
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
    await ai_orm_context_service_cache.set_models(response)
    return response
