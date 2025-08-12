from typing import Optional
from pydantic import BaseModel, UUID4


class PreparedIntegrationCreateRequest(BaseModel):
    organization_id: UUID4
    user_id: UUID4
    service_type: str
    auth_method: str
    connection_name: str
    host: str
    port: int
    database_name: str
    username: Optional[str]
    password: Optional[str]
    kerberos_principal: Optional[str]
    windows_domain: Optional[str]
    extra_options: Optional[str]
    autosync_on: bool
