from llm_inference_service.domain.models.model_gateway_params import (
    PlatformLlmParams,
    ProviderLlmParams,
    UserLlmParams,
)
from llm_inference_service.services.models_gateway.exceptions import (
    MissingModelProviderFactory,
)

from .factory import ProviderFactoryBase
from .registry import PROVIDER_FACTORY_REGISTRY


def dispatch_provider_factory(params: ProviderLlmParams) -> ProviderFactoryBase:
    match params:
        case PlatformLlmParams(provider=provider):
            if provider not in PROVIDER_FACTORY_REGISTRY:
                raise MissingModelProviderFactory(
                    f"Provider factory for {provider} not found"
                )
            return PROVIDER_FACTORY_REGISTRY[provider](model_meta=params.meta)
        case UserLlmParams():
            if "custom" not in PROVIDER_FACTORY_REGISTRY:
                raise MissingModelProviderFactory(
                    "Custom provider factory not registered"
                )
            return PROVIDER_FACTORY_REGISTRY["custom"](model_meta={"model": params})
