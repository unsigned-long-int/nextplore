from pydantic import BaseModel, Field
from typing import Optional


class IntegrationUpdateResponse(BaseModel):
    success: bool
    message: Optional[str] = Field(default=None)
    