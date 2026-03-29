from typing import Dict, Type

from .factory import (
    ProviderFactoryBase,
    HFProviderFactory,
    OpenAIProviderFactory,
    UserLlmProviderFactory
)


PROVIDER_FACTORY_REGISTRY: Dict[str, Type[ProviderFactoryBase]] = {
    'huggingface': HFProviderFactory,
    'openai': OpenAIProviderFactory,
    'custom': UserLlmProviderFactory
}



