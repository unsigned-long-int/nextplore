from typing import Optional
from datetime import datetime
from pydantic import BaseModel, UUID4, Field

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
    assigned_at: Optional[datetime] = Field(default=None)
    activated_at: Optional[datetime] = Field(default=None)
    revoked_at: Optional[datetime] = Field(default=None)
