from enum import StrEnum

from pydantic import UUID4, BaseModel


class LlmSource(StrEnum):
    user = "user"
    platform = "platform"


class ModelProfile(BaseModel):
    source: LlmSource
    provider: str
    model_id: str
    label: str
    model_ref_id: UUID4 | None
    tags: list[str]
