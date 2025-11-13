from pydantic import BaseModel


class VectorStatsResponse(BaseModel):
    vector_count: int
