from typing import Dict, Type

from services.context_providers.base import AIORMContextProviderBase
from services.context_providers.hugging_face import HuggingFaceORMContextProvider
from services.context_providers.open_ai import OpenAIORMContextProvider


PROVIDER_REGISTRY: Dict[str, Type[AIORMContextProviderBase]] = {
    'openai': OpenAIORMContextProvider,
    'huggingface': HuggingFaceORMContextProvider
}