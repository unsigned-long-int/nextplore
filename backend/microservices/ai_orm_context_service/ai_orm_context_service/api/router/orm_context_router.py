import logging
from fastapi import APIRouter, Depends, status, HTTPException
from svc_ai_orm_context_contracts.models import ORMContextResponse, ORMContextRequest

from ai_orm_context_service.api.context import get_current_identity
from ai_orm_context_service.services.orm_context.models_registry import get_models_registry, ModelsRegistry
from ai_orm_context_service.services.orm_context.provider_factory import dispatch_provider_factory
from ai_orm_context_service.services.orm_context.ai_adapter import adapt_llm_response
from ai_orm_context_service.services.orm_context.exceptions import InferenceProviderMissing, InvalidModelResponse
from ai_orm_context_service.cache import CacheService, get_cache_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])


@router.post('/context', response_model=ORMContextResponse)
async def get_orm_context(
    payload: ORMContextRequest, 
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service)
) -> ORMContextResponse:
    try:
        user_identity = get_current_identity()
        cached = await cache_service.get_orm_context(
            user_identity=user_identity,
            request=payload
        )
        if cached:
            return cached
        
        model_meta = models_registry.get_model(payload.provider, payload.model_id)
        provider_factory = dispatch_provider_factory(payload.provider, model_meta)
        provider = provider_factory.create()
        model_response = await provider.retrieve_model_response(payload)
        orm_context = adapt_llm_response(model_response)

        response = ORMContextResponse(
            integration=orm_context.integration,
            schema_name=orm_context.schema_name,
            class_name=orm_context.class_name,
            table_name=orm_context.table_name,
            column_names=orm_context.column_names,
            column_aggregates=orm_context.column_aggregates,
            column_filters=orm_context.column_filters
        )
        await cache_service.set_orm_context(
            user_identity=user_identity,
            request=payload,
            response=response
        )
        return response
    except (InferenceProviderMissing, InvalidModelResponse) as e:
        logger.error(f'Get context failed: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail={'message': str(e)}
        )
    except Exception as e:
        logger.error(f'Unexpected get context error: {e}', exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'message': f'Unexpected error: {str(e)}'}
        )
