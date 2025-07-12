from pydantic import BaseModel


class QueryVectorRequest(BaseModel):
    datastream: str
