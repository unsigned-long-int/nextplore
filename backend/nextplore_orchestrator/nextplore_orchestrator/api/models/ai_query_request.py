from pydantic import BaseModel
from enum import Enum

class QueryMode(str, Enum):
    SIMPLE = 'simple'
    EXPANDED = 'expanded'

class AIQueryRequest(BaseModel):
    provider: str
    model_id: str
    prompt: str
    mode: QueryMode = QueryMode.EXPANDED

