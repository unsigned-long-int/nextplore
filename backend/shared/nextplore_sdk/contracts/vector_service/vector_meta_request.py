from pydantic import BaseModel, UUID4
from typing import List


class VectorMetaRequest(BaseModel):
    vector_ids: List[UUID4]
