from typing import List
from pydantic import BaseModel 


class EmbeddingResponse(BaseModel):
    embedding: List[float]
    