from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from svc_integration_contracts.models import CertState


@dataclass(frozen=True)
class CertProfile:
    id: UUID
    state: CertState
    cert_kid: str
    cert_name: str
    public_cert_pem: str
    thumbprint_sha256: str
    not_before: datetime
    not_after: datetime
    created_at: datetime
    assigned_at: datetime | None = field(default=None)
    activated_at: datetime | None = field(default=None)
    revoked_at: datetime | None = field(default=None)
