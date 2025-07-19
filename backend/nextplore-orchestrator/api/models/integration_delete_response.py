from pydantic import BaseModel, Field
from typing import Optional


class IntegrationDeleteResponse(BaseModel):
    success: bool
    message: Optional[str] = Field(default=None)
    