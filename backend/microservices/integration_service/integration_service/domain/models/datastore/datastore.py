from dataclasses import dataclass, field
from uuid import UUID

from svc_integration_contracts.models import DB, Auth, Cloud


@dataclass(frozen=True)
class DataStore:
    id: UUID
    organization_id: UUID
    user_id: UUID
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    host: str
    database_name: str
    kek_kid: str
    port: int | None = field(default=None)
    warehouse: str | None = field(default=None)
    tenant_id: str | None = field(default=None)
    client_id: str | None = field(default=None)
    region: str | None = field(default=None)
    azure_cert_kid: str | None = field(default=None)
    azure_cert_name: str | None = field(default=None)
    azure_public_key_pem: str | None = field(default=None)
    snowflake_public_key_pem: str | None = field(default=None)
    autosync_on: bool = field(default=True)
