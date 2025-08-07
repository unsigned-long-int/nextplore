from typing import Optional
from pydantic import BaseModel, Field


class IntegrationMetadataResponse(BaseModel):
    service_type: str
    auth_method: str
    connection_name: str
    host: str
    port: int
    database_name: str
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    kerberos_principal: Optional[str] = Field(default=None)
    windows_domain: Optional[str] = Field(default=None)
    extra_options: Optional[str] = Field(default=None)
    autosync_on: bool
