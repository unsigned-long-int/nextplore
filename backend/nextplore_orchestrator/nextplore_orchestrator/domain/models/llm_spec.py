from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class UserLlmSpec:
    api_base: str
    connection_params: Dict[str, Any]
    max_tokens: int

@dataclass
class LlmSpec:
    provider: str
    model_id: str
    prompt: str
    user_llm_config: Optional[UserLlmSpec] = field(default=None)
