from abc import ABC, abstractmethod
from typing import Any

from llm_inference_service.domain.models.model_gateway_params import HFModel
from llm_inference_service.services.models_gateway.model_providers import (
    HFProvider,
    LiteLlmProvider,
    OpenAiProvider,
    UserLlmProvider,
)


class ProviderFactoryBase(ABC):
    def __init__(self, model_meta: dict[str, Any]) -> None:
        self.model_meta = model_meta

    @abstractmethod
    def create(self) -> LiteLlmProvider:
        pass


class HFProviderFactory(ProviderFactoryBase):
    def __init__(self, model_meta: dict[str, Any]) -> None:
        super().__init__(model_meta)

    def create(self) -> HFProvider:
        hf_model = HFModel(
            model_id=self.model_meta.get("model_id"),
            hf_path=self.model_meta.get("hf_path"),
            max_tokens=self.model_meta.get("max_tokens"),
            hf_url=self.model_meta.get("hf_url"),
        )
        return HFProvider(hf_model)


class OpenAIProviderFactory(ProviderFactoryBase):
    def __init__(self, model_meta: dict[str, Any]) -> None:
        super().__init__(model_meta)

    def create(self) -> OpenAiProvider:
        return OpenAiProvider(model_id=self.model_meta.get("model_id"))


class UserLlmProviderFactory(ProviderFactoryBase):
    def __init__(self, model_meta: dict[str, Any]) -> None:
        super().__init__(model_meta)

    def create(self) -> UserLlmProvider:
        return UserLlmProvider(model=self.model_meta.get("model"))
