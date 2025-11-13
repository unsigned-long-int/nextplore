from pydantic import BaseModel
from typing import List


class QDrantVectorRequest(BaseModel):
    embedding: List[float]
    