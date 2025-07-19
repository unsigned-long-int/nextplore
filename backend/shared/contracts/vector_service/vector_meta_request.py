from pydantic import BaseModel, UUID4
from typing import List


class VectorMetaRequest(BaseModel):
    integration_ids: List[UUID4]
