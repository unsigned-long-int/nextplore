from typing import Optional
from pydantic import BaseModel, Field

from nextplore_sdk.database.connection_maker.models.db import DB
from nextplore_sdk.database.connection_maker.models.auth import Auth
from nextplore_sdk.database.connection_maker.models.cloud import Cloud


class IntegrationConnectionProfile(BaseModel):
    auth: Auth
    cloud: Cloud
    db: DB
    host: str
    database_name: str 
    port: Optional[int] = Field(default=None)
    warehouse: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    client_secret: Optional[str] = Field(default=None)
    aws_external_id: Optional[str] = Field(default=None)
    aws_role_arn: Optional[str] = Field(default=None)
    azure_cert_kid: Optional[str] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None)
    client_id: Optional[str] = Field(default=None)
    region: Optional[str] = Field(default=None)
