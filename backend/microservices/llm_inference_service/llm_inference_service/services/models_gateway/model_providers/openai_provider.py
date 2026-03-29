import os
from typing import Dict, Any

import litellm
from pydantic import SecretStr

from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider


class OpenAiProvider(LiteLlmProvider):
    def __init__(self, model_id: str) -> None:
        super().__init__()
        self.model_id = model_id
        self._api_key = SecretStr(os.getenv('OPENAI_API_KEY', ''))

    def model_path(self) -> str:
        return f'openai/{self.model_id}'

    def base_kwargs(self) -> Dict[str, Any]:
        return {
            'model': self.model_path(),
            'api_key': self._api_key.get_secret_value(),
        }

    def max_tokens(self) -> int:
        info = litellm.get_model_info(self.model_path())
        return info.get('max_tokens') or 4096

