
from pydantic import UUID4, BaseModel


class QDrantVectorResponse(BaseModel):
    vector_ids: list[UUID4]
