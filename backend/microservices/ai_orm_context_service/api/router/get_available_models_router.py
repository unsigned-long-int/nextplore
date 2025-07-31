from fastapi import APIRouter

from shared.contracts.ai_orm_context_service import ModelInfo, AvailableModelsResponse
from shared.cache.service_caches.ai_orm_context_cache import ai_orm_context_service_cache
from services.model_registry import ModelRegistry

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])

@router.get('/get-models', response_model=AvailableModelsResponse)
async def get_models() -> AvailableModelsResponse:
    cached = await ai_orm_context_service_cache.get_models()
    if cached:
        return cached
    
    registry = ModelRegistry()
    models = []
    for model_id, meta in registry.all().items():
        models.append(ModelInfo(
            model_id=model_id,
            label=meta.get('label', model_id),
            tags=meta.get('tags', [])
        ))

    response = AvailableModelsResponse(models=models)
    await ai_orm_context_service_cache.set_models(response)
    return response
