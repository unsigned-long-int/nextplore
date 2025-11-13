from dataclasses import dataclass, field
from typing import Optional

from .db import DB
from .auth import Auth
from .cloud import Cloud


@dataclass(frozen=True)
class ConnectionProfile:
    cloud: Cloud
    auth: Auth
    db: DB
    host: str
    database: str
    port: Optional[int] = field(default=None)
    warehouse: Optional[str] = field(default=None)
    username: Optional[str] = field(default=None)
    password: Optional[str] = field(default=None)
    client_secret: Optional[str] = field(default=None)
    aws_external_id: Optional[str] = field(default=None)
    aws_role_arn: Optional[str] = field(default=None)
    azure_cert_kid: Optional[str] = field(default=None)
    azure_cert_name: Optional[str] = field(default=None)
    tenant_id: Optional[str] = field(default=None)
    client_id: Optional[str] = field(default=None)
    snowflake_private_key: Optional[str] = field(default=None)
    region: Optional[str] = field(default=None)
