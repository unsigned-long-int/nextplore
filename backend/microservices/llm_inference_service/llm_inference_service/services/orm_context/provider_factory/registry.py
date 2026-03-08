from typing import Dict, Type

from .factory import ProviderFactoryBase, HFProviderFactory, OpenAIProviderFactory


PROVIDER_FACTORY_REGISTRY: Dict[str, Type[ProviderFactoryBase]] = {
    'huggingface': HFProviderFactory,
    'openai': OpenAIProviderFactory
}



