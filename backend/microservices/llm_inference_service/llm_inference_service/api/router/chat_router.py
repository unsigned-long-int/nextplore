import logging
from uuid import UUID
from fastapi import APIRouter, status, HTTPException, Depends

from llm_inference_service.api.context import get_current_identity
from llm_inference_service.cache import CacheService, get_cache_service
from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing
from llm_inference_service.services.models_gateway.models_registry import get_models_registry, ModelsRegistry
from llm_inference_service.services.models_gateway.provider_factory import dispatch_provider_factory


from svc_llm_inference_contracts.models import PromptRequest, PromptResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/llm-inference', tags=['Chat'])


@router.post('/organizations/{organization_id}/users/{user_id}/chat', response_model=PromptResponse)
async def get_prompt_response(
    organization_id: UUID,
    user_id: UUID,
    payload: PromptRequest,
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service),

) -> PromptResponse:
    user_identity = get_current_identity()

    if organization_id != user_identity.organization_id or user_id != user_identity.user_id:
        logger.error(
            'Forbidden request',
            extra={'ord_id': organization_id, 'user_id': user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'message': 'Forbidden'}
        )

    try:
        cached = await cache_service.get_prompt_response(
            user_identity=user_identity,
            request=payload
        )

        if cached:
            return cached

        model_meta, provider_name = models_registry.get_default_model_config()
        provider_factory = dispatch_provider_factory(provider_name, model_meta)
        provider = provider_factory.create()
        response = await provider.prompt_model(payload.prompt)

        prompt_response = PromptResponse(
            response=response
        )
        await cache_service.set_prompt_response(
            user_identity=user_identity,
            request=payload,
            response=prompt_response
        )
        return prompt_response
    except InferenceProviderMissing as e:
        logger.error(f'Prompt response failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Unexpected get prompt response error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

