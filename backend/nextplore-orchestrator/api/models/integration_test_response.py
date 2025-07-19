from pydantic import BaseModel, Field
from typing import Optional


class IntegrationTestResponse(BaseModel):
    success: bool
    message: Optional[str] = Field(default=None)
    