from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Cert:
    cert_kid: str
    cert_name: str
    public_cert_pem: str
    thumbprint_sha256: str
    not_before: datetime
    not_after: datetime
