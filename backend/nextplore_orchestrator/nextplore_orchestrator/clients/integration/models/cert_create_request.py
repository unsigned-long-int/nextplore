from typing import Optional
from pydantic import BaseModel, Field


class CertCreateRequest(BaseModel):
    purpose: Optional[str] = Field(default=None)
    key_size: Optional[int] = Field(default=None)
    validity_in_months: Optional[int] = Field(default=None)
