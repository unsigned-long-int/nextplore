from typing import Dict, Any
from abc import ABC, abstractmethod

from llm_inference_service.domain.models.hf_model import HFModel
from llm_inference_service.services.models_gateway.model_providers.hugging_face.inference.inference_provider_factory import dispatch_inference_provider
from llm_inference_service.services.models_gateway.model_providers.base import BaseProvider
from llm_inference_service.services.models_gateway.model_providers.hugging_face import HFProvider
from llm_inference_service.services.models_gateway.model_providers.openai import OpenAIProvider


class ProviderFactoryBase(ABC):
    def __init__(self, model_meta: Dict[str, Any]) -> None:
        self.model_meta = model_meta

    @abstractmethod
    def create(self) -> BaseProvider:
        pass


class HFProviderFactory(ProviderFactoryBase):
    def __init__(self, model_meta: Dict[str, Any]) -> None:
        super().__init__(model_meta)

    def create(self) -> HFProvider:
        hf_model = HFModel(
            model_id=self.model_meta.get('model_id'),
            hf_path=self.model_meta.get('hf_path'),
            max_tokens=self.model_meta.get('max_tokens')
        )
        inference = dispatch_inference_provider(
            inference=self.model_meta.get('inference'),
            url=self.model_meta.get('hf_url')
        )
        return HFProvider(
            model=hf_model,
            inference_provider=inference
        )
    

class OpenAIProviderFactory(ProviderFactoryBase):
    def __init__(self, model_meta: Dict[str, Any]) -> None:
        super().__init__(model_meta)

    def create(self) -> OpenAIProvider:
        return OpenAIProvider(
            model_id=self.model_meta.get('model_id')
        )
