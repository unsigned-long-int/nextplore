from typing import Dict, Any

from llm_inference_service.domain.models.model_gateway_params import UserLlm
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import LiteLlmProvider


class UserLlmProvider(LiteLlmProvider):
    def __init__(self, model: UserLlm) -> None:
        super().__init__()
        self.model = model

    def model_path(self) -> str:
        return f'openai/{self.model.model_id}'

    def base_kwargs(self) -> Dict[str, Any]:
        return {
            'model': self.model_path(),
            **self.model.connection_params
        }

    def max_tokens(self) -> int:
        return self.model.max_tokens
