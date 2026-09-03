import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from svc_llm_inference_contracts.models import ORMContextRequest, ORMContextResponse

from llm_inference_service.api.context import get_current_identity
from llm_inference_service.cache import CacheService, get_cache_service
from llm_inference_service.domain.mappers.model_gateway_params import (
    resolve_llm_provider_params,
)
from llm_inference_service.services.models_gateway.exceptions import (
    InferenceProviderMissing,
    InvalidModelResponse,
)
from llm_inference_service.services.models_gateway.models_registry import (
    ModelsRegistry,
    get_models_registry,
)
from llm_inference_service.services.models_gateway.provider_factory import (
    dispatch_provider_factory,
)
from llm_inference_service.services.rag_pipeline.ai_adapter import adapt_llm_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/llm-inference", tags=["AIORMContext"])


@router.post(
    "/organizations/{organization_id}/users/{user_id}/context",
    response_model=ORMContextResponse,
)
async def get_orm_context(
    organization_id: UUID,
    user_id: UUID,
    payload: ORMContextRequest,
    models_registry: ModelsRegistry = Depends(get_models_registry),
    cache_service: CacheService = Depends(get_cache_service),
) -> ORMContextResponse:
    user_identity = get_current_identity()

    if (
        organization_id != user_identity.organization_id
        or user_id != user_identity.user_id
    ):
        logger.error(
            "Forbidden request", extra={"org_id": organization_id, "user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail={"message": "Forbidden"}
        )

    try:
        cached = await cache_service.get_orm_context(
            user_identity=user_identity, request=payload
        )
        if cached:
            return cached

        llm_provider_params = resolve_llm_provider_params(
            payload=payload,
            models_registry=models_registry,
        )
        provider_factory = dispatch_provider_factory(llm_provider_params)
        provider = provider_factory.create()
        model_response = await provider.execute_structured_query(payload)
        orm_context = adapt_llm_response(model_response)

        response = ORMContextResponse(
            datastore=orm_context.datastore,
            schema_name=orm_context.schema_name,
            class_name=orm_context.class_name,
            table_name=orm_context.table_name,
            column_names=orm_context.column_names,
            column_aggregates=orm_context.column_aggregates,
            column_filters=orm_context.column_filters,
        )
        await cache_service.set_orm_context(
            user_identity=user_identity, request=payload, response=response
        )
        return response
    except (InferenceProviderMissing, InvalidModelResponse) as e:
        logger.error(f"Get context failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY, detail={"message": str(e)}
        )
    except Exception as e:
        logger.error(f"Unexpected get context error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": f"Unexpected error: {e!s}"},
        )
