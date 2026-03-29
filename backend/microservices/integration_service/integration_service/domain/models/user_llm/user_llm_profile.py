from dataclasses import dataclass


@dataclass(frozen=True)
class UserLlmProfile:
    api_base: str
    model_id: str
    label: str
    max_tokens: int
