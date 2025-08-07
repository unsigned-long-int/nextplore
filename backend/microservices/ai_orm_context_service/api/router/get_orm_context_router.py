import logging
from fastapi import APIRouter, Depends

from services.models_registry import get_models_registry, ModelsRegistry
from services.provider_factory import dispatch_provider_factory
from services.orm_context_builder.ai_adapter import adapt_llm_response
from nextplore_shared.contracts.ai_orm_context_service.orm_context_request import ORMContextRequest
from nextplore_shared.contracts.ai_orm_context_service.orm_context_response import ORMContextResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix='/v1/ai-orm', tags=['AIORMContext'])

@router.post('/get-context', response_model=ORMContextResponse)
async def get_orm_context(
    payload: ORMContextRequest, 
    models_registry: ModelsRegistry = Depends(get_models_registry)
) -> ORMContextResponse:
    try:
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
        return response
    except Exception as e:
        logger.error(f'get context failed: {e}', exc_info=True)
