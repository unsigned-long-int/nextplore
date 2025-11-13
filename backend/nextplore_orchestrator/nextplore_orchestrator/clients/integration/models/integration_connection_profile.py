from typing import Optional
from pydantic import BaseModel, Field, SecretStr, field_serializer

from .auth import Auth
from .cloud import Cloud
from .db import DB


class IntegrationConnectionProfile(BaseModel):
    auth: Auth
    cloud: Cloud
    db: DB
    host: str
    database_name: str
    port: Optional[int] = Field(default=None)
    warehouse: Optional[str] = Field(default=None)
    username: Optional[SecretStr] = Field(default=None)
    password: Optional[SecretStr] = Field(default=None)
    client_secret: Optional[SecretStr] = Field(default=None)
    aws_external_id: Optional[SecretStr] = Field(default=None)
    aws_role_arn: Optional[SecretStr] = Field(default=None)
    snowflake_private_key: Optional[SecretStr] = Field(default=None)
    azure_cert_kid: Optional[str] = Field(default=None)
    azure_cert_name: Optional[str] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)

    @field_serializer(
        'username',
        'password',
        'client_secret',
        'aws_external_id',
        'aws_role_arn',
        'snowflake_private_key',
        when_used='json'
    )
    def _expose_secret(self, value: Optional[SecretStr]) -> Optional[str]:
        return value.get_secret_value() if value else None
