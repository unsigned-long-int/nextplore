from dataclasses import dataclass, field

from .auth import Auth
from .cloud import Cloud
from .db import DB


@dataclass(frozen=True)
class ConnectionProfile:
    cloud: Cloud
    auth: Auth
    db: DB
    host: str
    database: str
    port: int | None = field(default=None)
    warehouse: str | None = field(default=None)
    username: str | None = field(default=None)
    password: str | None = field(default=None)
    client_secret: str | None = field(default=None)
    aws_external_id: str | None = field(default=None)
    aws_role_arn: str | None = field(default=None)
    azure_cert_kid: str | None = field(default=None)
    azure_cert_name: str | None = field(default=None)
    tenant_id: str | None = field(default=None)
    client_id: str | None = field(default=None)
    snowflake_private_key: str | None = field(default=None)
    region: str | None = field(default=None)
