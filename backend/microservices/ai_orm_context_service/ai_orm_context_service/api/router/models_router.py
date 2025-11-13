import logging
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException

from ai_orm_context_service.api.models.model_info import ModelInfo
from ai_orm_context_service.cache import CacheService, get_cache_service
from ai_orm_context_service.services.orm_context.models_registry import ModelsRegistry, get_models_registry


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])


@router.get('/models', response_model=List[ModelInfo])
async def get_models(
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[ModelInfo]:
    try:
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

        response = models
        await cache_service.set_models(response)
        return response
    except Exception as e:
        logger.error(f'Unexpected get models error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
