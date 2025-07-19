from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class DecryptedIntegration:
    organization_id: UUID
    user_id: UUID
    service_type: str
    auth_method: str
    connection_name: str
    host: str
    port: int
    database_name: str
    autosync_on: bool
    integration_id: Optional[UUID] = field(default=None)
    username: Optional[str] = field(default=None)
    password: Optional[str] = field(default=None)
    kerberos_principal: Optional[str] = field(default=None)
    windows_domain: Optional[str] = field(default=None)
    extra_options: Optional[str] = field(default=None)
