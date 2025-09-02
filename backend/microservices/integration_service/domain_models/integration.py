from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime

from .auth import Auth
from .cloud import Cloud
from .db import DB


@dataclass
class Integration:
    organization_id: UUID
    user_id: UUID
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    host: str
    database_name: str
    port: Optional[int] = field(default=None)
    warehouse: Optional[str] = field(default=None)
    tenant_id: Optional[str] = field(default=None)
    client_id: Optional[str] = field(default=None)
    region: Optional[str] = field(default=None)
    azure_cert_kid: Optional[str] = field(default=None)
    azure_public_key_pem: Optional[str] = field(default=None)
    snowflake_public_key_pem: Optional[str] = field(default=None)
    autosync_on: bool = field(default=True)

