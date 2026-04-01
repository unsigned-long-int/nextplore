from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserLlmProfile:
    api_base: str
    model_id: str
    label: str
    max_tokens: int
    model_ref_id: UUID
