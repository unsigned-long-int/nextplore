from typing import Any

from llm_inference_service.domain.models.model_gateway_params import UserLlmParams
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import (
    LiteLlmProvider,
)


class UserLlmProvider(LiteLlmProvider):
    def __init__(self, model: UserLlmParams) -> None:
        super().__init__()
        self.model = model

    def model_path(self) -> str:
        return f"openai/{self.model.model_id}"

    def base_kwargs(self) -> dict[str, Any]:
        return {
            "model": self.model_path(),
            "api_base": self.model.api_base,
            **self.model.connection_params,
        }

    def max_tokens(self) -> int:
        return self.model.max_tokens
