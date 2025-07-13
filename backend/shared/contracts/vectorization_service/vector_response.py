from typing import List
from pydantic import BaseModel 


class VectorResponse(BaseModel):
    vector: List[float]
    