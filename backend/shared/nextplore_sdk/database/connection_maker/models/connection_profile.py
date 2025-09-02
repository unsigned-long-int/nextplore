from dataclasses import dataclass, field
from typing import Optional, Dict

from connection_maker.models.auth import Auth
from connection_maker.models.cloud import Cloud
from connection_maker.models.db import DB


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
    tenant_id: Optional[str] = field(default=None)
    client_id: Optional[str] = field(default=None)
    snowflake_private_key: Optional[str] = field(default=None)
    region: Optional[str] = field(default=None)
    nonce: Optional[bytes] = field(default=None)
    tag: Optional[bytes] = field(default=None)
    kek_kid: Optional[str] = field(default=None)
    enc_alg: Optional[str] = field(default=None)
    wrap_alg: Optional[str] = field(default=None)
    aad: Optional[Dict[str, str]] = field(default=None)
    encoding: Optional[str] = field(default=None)
    ca_path: Optional[str] = field(default=None)
