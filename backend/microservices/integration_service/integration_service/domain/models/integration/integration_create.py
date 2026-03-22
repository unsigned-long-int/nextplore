from typing import Optional
from dataclasses import dataclass, field
from svc_integration_contracts.models import DB, Auth, Cloud


@dataclass(frozen=True)
class IntegrationCreate:
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    descr: str
    host: str
    database_name: str
    kek_kid: str
    port: Optional[int] = field(default=None)
    warehouse: Optional[str] = field(default=None)
    tenant_id: Optional[str] = field(default=None)
    client_id: Optional[str] = field(default=None)
    region: Optional[str] = field(default=None)
    azure_cert_kid: Optional[str] = field(default=None)
    azure_cert_name: Optional[str] = field(default=None)
    azure_public_key_pem: Optional[str] = field(default=None)
    snowflake_public_key_pem: Optional[str] = field(default=None)
    autosync_on: bool = field(default=True)
