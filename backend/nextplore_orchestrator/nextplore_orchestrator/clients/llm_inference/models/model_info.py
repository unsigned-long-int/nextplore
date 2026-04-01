from pydantic import BaseModel, UUID4
from typing import List, Optional
from enum import StrEnum

class LlmSource(StrEnum):
    user = 'user'
    platform = 'platform'

class ModelProfile(BaseModel):
    source: LlmSource
    provider: str
    model_id: str
    label: str
    model_ref_id: Optional[UUID4]
    tags: List[str]
