from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class EncryptedIntegration:
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
    encrypted_username: Optional[str] = field(default=None)
    encrypted_password: Optional[str] = field(default=None)
    encrypted_kerberos_principal: Optional[str] = field(default=None)
    encrypted_windows_domain: Optional[str] = field(default=None)
    encrypted_extra_options: Optional[str] = field(default=None)
