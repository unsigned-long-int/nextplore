from pydantic import BaseModel, UUID4, Field
from enum import StrEnum
from typing import Optional

class QueryMode(StrEnum):
    SIMPLE = 'simple'
    EXPANDED = 'expanded'

class AIQueryRequest(BaseModel):
    provider: str
    model_id: str
    prompt: str
    is_user_model: bool
    model_ref_id: Optional[UUID4] = Field(..., title="Model Ref Id")
    mode: QueryMode = QueryMode.EXPANDED
    bypass_cache: bool = Field(default=False, title="Bypass Cache")
