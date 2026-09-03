from typing import Any

from svc_llm_inference_contracts.models import (
    MultiQueryRequest,
    ORMContextRequest,
    UserLlmTestRequest,
)

from llm_inference_service.domain.models.model_gateway_params import (
    PlatformLlmParams,
    ProviderLlmParams,
    UserLlmParams,
)
from llm_inference_service.services.models_gateway.models_registry import ModelsRegistry


def user_llm_params_from_dto(
    user_llm_test_request: UserLlmTestRequest,
) -> UserLlmParams:
    return UserLlmParams(
        model_id=user_llm_test_request.model_id,
        api_base=user_llm_test_request.api_base,
        connection_params=user_llm_test_request.connection_params,
        max_tokens=user_llm_test_request.max_tokens,
    )


def resolve_llm_provider_params(
    payload: MultiQueryRequest | ORMContextRequest,
    models_registry: ModelsRegistry,
) -> ProviderLlmParams:
    if payload.user_llm_config is not None:
        return UserLlmParams(
            model_id=payload.model_id,
            api_base=payload.user_llm_config.api_base,
            connection_params=payload.user_llm_config.connection_params,
            max_tokens=payload.user_llm_config.max_tokens,
        )

    model_meta = models_registry.get_model(payload.provider, payload.model_id)
    return PlatformLlmParams(
        model_id=payload.model_id,
        provider=payload.provider,
        meta=model_meta,
    )


def llm_provider_params_from_config(
    provider_name: str, model_meta: dict[str, Any]
) -> ProviderLlmParams:
    return PlatformLlmParams(
        model_id=model_meta["model_id"],
        provider=provider_name,
        meta=model_meta,
    )
