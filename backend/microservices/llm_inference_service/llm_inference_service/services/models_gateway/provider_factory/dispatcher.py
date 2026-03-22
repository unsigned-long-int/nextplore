from typing import Dict, Any

from llm_inference_service.services.models_gateway.exceptions import MissingModelProviderFactory

from .factory import ProviderFactoryBase
from .registry import PROVIDER_FACTORY_REGISTRY


def dispatch_provider_factory(provider: str, model_meta: Dict[str, Any]) -> ProviderFactoryBase:
    if provider not in PROVIDER_FACTORY_REGISTRY:
        msg = f'Model provider factory for provider: {provider} not found'
        raise MissingModelProviderFactory(msg)
    provider_cls = PROVIDER_FACTORY_REGISTRY.get(provider)
    return provider_cls(model_meta)
