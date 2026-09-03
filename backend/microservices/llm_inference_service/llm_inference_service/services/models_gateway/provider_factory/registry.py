
from .factory import (
    HFProviderFactory,
    OpenAIProviderFactory,
    ProviderFactoryBase,
    UserLlmProviderFactory,
)

PROVIDER_FACTORY_REGISTRY: dict[str, type[ProviderFactoryBase]] = {
    "huggingface": HFProviderFactory,
    "openai": OpenAIProviderFactory,
    "custom": UserLlmProviderFactory,
}
