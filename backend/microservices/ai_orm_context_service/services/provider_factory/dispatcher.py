from typing import Dict, Any

from .factory import ProviderFactoryBase
from .registry import PROVIDER_FACTORY_REGISTRY
from .exceptions import MissingModelProviderFactory


def dispatch_provider_factory(provider: str, model_meta: Dict[str, Any]) -> ProviderFactoryBase:
    if provider not in PROVIDER_FACTORY_REGISTRY:
        msg = f'Model provider factory for provider: {provider} not found'
        raise MissingModelProviderFactory(msg)
    provider_cls = PROVIDER_FACTORY_REGISTRY.get(provider)
    print(f'provider received: {provider_cls}')
    return provider_cls(model_meta)