from typing import Dict, Any, Union
from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformLlmParams:
    provider: str
    model_id: str
    meta: Dict[str, Any]


@dataclass(frozen=True)
class UserLlmParams:
    model_id: str
    api_base: str
    connection_params: Dict[str, Any]
    max_tokens: int = 4096


ProviderLlmParams = Union[PlatformLlmParams, UserLlmParams]