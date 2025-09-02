from typing import Optional
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime


@dataclass
class EncryptedIntegration:
    organization_id: UUID
    user_id: UUID
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    host: str
    database_name: str
    autosync_on: bool
    created_at: datetime
    updated_at: datetime
    port: Optional[int] = field(default=None)
    warehouse: Optional[str] = field(default=None)
    tenant_id: Optional[str] = field(default=None)
    client_id: Optional[str] = field(default=None)
    region: Optional[str] = field(default=None)
    azure_cert_kid: Optional[str] = field(default=None)
    azure_public_key_pem: Optional[str] = field(default=None)
    snowflake_public_key_pem: Optional[str] = field(default=None)
    username_secret_id: Optional[UUID] = field(default=None)
    password_secret_id: Optional[UUID] = field(default=None)
    client_secret_id: Optional[UUID] = field(default=None)
    aws_role_arn_secret_id: Optional[UUID] = field(default=None)
    aws_external_id_secret_id: Optional[UUID] = field(default=None)
    snowflake_private_key_secret_id: Optional[UUID] = field(default=None)
