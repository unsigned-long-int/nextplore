from pydantic import BaseModel, Field, SecretStr, field_serializer

from .auth import Auth
from .cloud import Cloud
from .db import DB


class IntegrationCreateRequest(BaseModel):
    auth: Auth
    cloud: Cloud
    db: DB
    connection_name: str
    descr: str
    host: str
    database_name: str
    port: int | None = Field(default=None)
    warehouse: str | None = Field(default=None)
    tenant_id: str | None = Field(default=None)
    client_id: str | None = Field(default=None)
    region: str | None = Field(default=None)
    kek_kid: str | None = Field(default=None)
    azure_cert_kid: str | None = Field(default=None)
    azure_cert_name: str | None = Field(default=None)
    azure_public_key_pem: str | None = Field(default=None)
    snowflake_public_key_pem: str | None = Field(default=None)
    username: SecretStr | None = Field(default=None)
    password: SecretStr | None = Field(default=None)
    client_secret: SecretStr | None = Field(default=None)
    aws_role_arn: SecretStr | None = Field(default=None)
    aws_external_id: SecretStr | None = Field(default=None)
    snowflake_private_key: SecretStr | None = Field(default=None)
    autosync_on: bool = Field(default=True)

    @field_serializer(
        "username",
        "password",
        "client_secret",
        "aws_external_id",
        "aws_role_arn",
        "snowflake_private_key",
        when_used="json",
    )
    def _expose_secret(self, value: SecretStr | None) -> str | None:
        return value.get_secret_value() if value else None
