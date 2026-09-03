from enum import StrEnum

from pydantic import UUID4, BaseModel, Field


class QueryMode(StrEnum):
    SIMPLE = "simple"
    EXPANDED = "expanded"


class AIQueryRequest(BaseModel):
    provider: str
    model_id: str
    prompt: str
    is_user_model: bool
    model_ref_id: UUID4 | None = Field(..., title="Model Ref Id")
    mode: QueryMode = QueryMode.EXPANDED
    bypass_cache: bool = Field(default=False, title="Bypass Cache")
