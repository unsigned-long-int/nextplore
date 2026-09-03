
from pydantic import BaseModel


class QDrantVectorRequest(BaseModel):
    embedding: list[float]
