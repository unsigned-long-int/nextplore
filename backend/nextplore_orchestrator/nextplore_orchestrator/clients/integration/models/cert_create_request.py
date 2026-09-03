from pydantic import BaseModel, Field


class CertCreateRequest(BaseModel):
    purpose: str | None = Field(default=None)
    key_size: int | None = Field(default=None)
    validity_in_months: int | None = Field(default=None)
