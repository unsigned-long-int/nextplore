import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, status, HTTPException

from svc_llm_inference_contracts.models import ModelInfo
from llm_inference_service.api.context import get_current_identity
from llm_inference_service.cache import CacheService, get_cache_service
from llm_inference_service.services.models_gateway.models_registry import ModelsRegistry, get_models_registry


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/llm-inference', tags=['AIORMContext'])


@router.get('/organizations/{organization_id}/users/{user_id}/models', response_model=List[ModelInfo])
async def get_models(
    organization_id: UUID,
    user_id: UUID,
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service)
) -> List[ModelInfo]:
    user_identity = get_current_identity()

    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'org_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )

    try:
        cached = await cache_service.get_models(user_identity)
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
        await cache_service.set_models(user_identity=user_identity, response=response)
        return response
    except Exception as e:
        logger.error(f'Unexpected get models error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
