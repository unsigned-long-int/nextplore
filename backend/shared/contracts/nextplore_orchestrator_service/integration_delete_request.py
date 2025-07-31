from pydantic import BaseModel


class IntegrationDeleteRequest(BaseModel):
    id: str
    