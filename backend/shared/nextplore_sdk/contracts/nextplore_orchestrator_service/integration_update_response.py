from pydantic import BaseModel


class IntegrationUpdateResponse(BaseModel):
    success: bool
    