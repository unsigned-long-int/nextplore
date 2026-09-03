from dataclasses import dataclass
from typing import Any, Union


@dataclass(frozen=True)
class PlatformLlmParams:
    provider: str
    model_id: str
    meta: dict[str, Any]


@dataclass(frozen=True)
class UserLlmParams:
    model_id: str
    api_base: str
    connection_params: dict[str, Any]
    max_tokens: int = 4096


ProviderLlmParams = Union[PlatformLlmParams, UserLlmParams]
