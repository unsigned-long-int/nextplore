from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class UserLlm:
    model_id: str
    api_base: str
    connection_params: Dict[str, Any]
    max_tokens: int = 4096
