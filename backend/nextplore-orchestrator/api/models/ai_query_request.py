from pydantic import BaseModel
from typing import Optional

class AIQueryRequest(BaseModel):
    prompt: str
