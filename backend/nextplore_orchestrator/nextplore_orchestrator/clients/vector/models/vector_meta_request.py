
from pydantic import UUID4, BaseModel


class VectorMetaRequest(BaseModel):
    vector_ids: list[UUID4]
