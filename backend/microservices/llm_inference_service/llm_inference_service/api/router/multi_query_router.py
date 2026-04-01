import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from svc_llm_inference_contracts.models import MultiQueryRequest, MultiQueryResponse

from llm_inference_service.api.context import get_current_identity
from llm_inference_service.cache import CacheService, get_cache_service
from llm_inference_service.domain.mappers.model_gateway_params import resolve_llm_provider_params
from llm_inference_service.services.models_gateway.models_registry import get_models_registry, ModelsRegistry
from llm_inference_service.services.models_gateway.exceptions import InferenceProviderMissing, InvalidModelResponse
from llm_inference_service.services.models_gateway.provider_factory import dispatch_provider_factory
from llm_inference_service.services.rag_pipeline.decomposition.multi_query_creator import expand_query

logger  = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/llm-inference', tags=['QueryMultiplier'])


@router.post('/organizations/{organization_id}/users/{user_id}/query_multiplier', response_model=MultiQueryResponse)
async def get_expanded_query(
    organization_id: UUID,
    user_id: UUID,
    payload: MultiQueryRequest,
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service),
) -> MultiQueryResponse:
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
        cached = await cache_service.get_expanded_query(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached

        llm_provider_params = resolve_llm_provider_params(
            payload=payload,
            models_registry=models_registry,
        )
        provider_factory = dispatch_provider_factory(llm_provider_params)
        provider = provider_factory.create()
        expanded_query = expand_query(payload.query, payload.multiplier)
        query_response = await provider.execute_query(expanded_query)
        variants = [q.strip() for q in query_response.strip().splitlines() if q.strip()]

        multi_query_response = MultiQueryResponse(
            variants=[payload.query] + variants[:payload.multiplier]
        )
        await cache_service.set_expanded_query(
            user_identity=user_identity,
            request=payload,
            response=multi_query_response,
        )
        return multi_query_response
    except (InferenceProviderMissing, InvalidModelResponse) as e:
        logger.error(f'Get multi query failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Unexpected get multi query error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )

