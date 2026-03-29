import os
from typing import Dict, Any
from pydantic import SecretStr

from llm_inference_service.domain.models.model_gateway_params import HFModel
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider


class HFProvider(LiteLlmProvider):
    def __init__(self, model: HFModel) -> None:
        super().__init__()
        self.model = model
        self._api_key = SecretStr(os.getenv('HUGGINGFACE_API_KEY', ''))

    def model_path(self) -> str:
        return f'openai/{self.model.hf_path}'

    def base_kwargs(self) -> Dict[str, Any]:
        return {
            'model': self.model_path(),
            'api_key': self._api_key.get_secret_value(),
            'api_base': self.model.hf_url,
        }

    def max_tokens(self) -> int:
        return self.model.max_tokens
