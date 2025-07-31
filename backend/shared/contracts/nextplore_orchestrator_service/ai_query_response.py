from pydantic import BaseModel
from typing import List, Dict

class AIQueryResponse(BaseModel):
    sql: str
    data: List[Dict[str, str]]