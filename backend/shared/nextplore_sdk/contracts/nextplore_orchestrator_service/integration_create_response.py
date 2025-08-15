from pydantic import BaseModel


class IntegrationCreateResponse(BaseModel):
    success: bool

    