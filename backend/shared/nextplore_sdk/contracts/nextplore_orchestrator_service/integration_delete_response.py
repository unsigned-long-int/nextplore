from pydantic import BaseModel


class IntegrationDeleteResponse(BaseModel):
    success: bool
    