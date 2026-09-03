from pydantic import BaseModel


class EmbeddingResponse(BaseModel):
    embedding: list[float]
