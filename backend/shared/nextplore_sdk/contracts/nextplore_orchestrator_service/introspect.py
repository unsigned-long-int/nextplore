from pydantic import BaseModel


class IntrospectRequest(BaseModel):
    db_url: str
    connection_id: str