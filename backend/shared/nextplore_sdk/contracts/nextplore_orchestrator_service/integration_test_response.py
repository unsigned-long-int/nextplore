from pydantic import BaseModel


class IntegrationTestResponse(BaseModel):
    success: bool
