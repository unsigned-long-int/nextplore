from typing import Any

from llm_inference_service.domain.models.model_gateway_params import UserLlmParams
from llm_inference_service.services.models_gateway.model_providers.lite_llm_provider import (
    LiteLlmProvider,
)
from llm_inference_service.services.models_gateway.security import assert_safe_api_base


_BLOCKED_OVERRIDE_KEYS: set[str] = {"api_base", "base_url", "model", "timeout"}

class UserLlmProvider(LiteLlmProvider):
    def __init__(self, model: UserLlmParams) -> None:
        super().__init__()
        self.model = model

    def model_path(self) -> str:
        return f"openai/{self.model.model_id}"

    def base_kwargs(self) -> dict[str, Any]:
        assert_safe_api_base(self.model.api_base)
        safe_overrides = {
            k: v
            for k, v in self.model.connection_params.items()
            if k not in _BLOCKED_OVERRIDE_KEYS
        }
        return {
            **safe_overrides,
            "model": self.model_path(),
            "api_base": self.model.api_base,
        }

    def max_tokens(self) -> int:
        return self.model.max_tokens
