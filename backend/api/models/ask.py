from pydantic import BaseModel
from typing import List, Dict

class AskRequest(BaseModel):
    prompt: str
    db_id: str

class AskResponse(BaseModel):
    sql: str
    data: List[Dict[str, str]]