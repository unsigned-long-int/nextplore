from services.context_providers.base import AIORMContextProviderBase
from services.model_registry import ModelRegistry
from .provider_registry import PROVIDER_REGISTRY


class ProviderNotFound(Exception):
    pass


def dispatch_context_provider(model_id: str) -> AIORMContextProviderBase:
    model_registry = ModelRegistry()
    model = model_registry.get_model(model_id)
    provider_name = model.get('provider').lower()
    provider_cls = PROVIDER_REGISTRY.get(provider_name)

    if provider_cls is None:
        raise ProviderNotFound(f'Provider was not found: {provider_name}')

    return provider_cls(model_id)
