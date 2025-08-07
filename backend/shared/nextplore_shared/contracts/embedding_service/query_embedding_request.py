from pydantic import BaseModel


class QueryEmbeddingRequest(BaseModel):
    datastream: str
