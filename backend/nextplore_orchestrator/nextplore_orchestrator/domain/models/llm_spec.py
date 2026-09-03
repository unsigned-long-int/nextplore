from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserLlmSpec:
    api_base: str
    connection_params: dict[str, Any]
    max_tokens: int


@dataclass
class LlmSpec:
    provider: str
    model_id: str
    prompt: str
    user_llm_config: UserLlmSpec | None = field(default=None)
    base_prompt_embedding: list[float] | None = field(default=None)
