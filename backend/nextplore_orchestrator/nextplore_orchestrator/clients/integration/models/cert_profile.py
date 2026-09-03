from datetime import datetime

from pydantic import UUID4, BaseModel, Field

from .cert_state import CertState


class CertProfile(BaseModel):
    id: UUID4
    state: CertState
    cert_kid: str
    cert_name: str
    public_cert_pem: str
    thumbprint_sha256: str
    not_before: datetime
    not_after: datetime
    created_at: datetime
    assigned_at: datetime | None = Field(default=None)
    activated_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)
