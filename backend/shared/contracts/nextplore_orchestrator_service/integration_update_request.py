from pydantic import BaseModel
from typing import Optional


class IntegrationUpdateRequest(BaseModel):
    id: str
    service_type: Optional[str] = None
    auth_method: Optional[str] = None
    connection_name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    kerberos_principal: Optional[str] = None
    windows_domain: Optional[str] = None
    extra_options: Optional[str] = None
    autosync_on: Optional[bool] = None
