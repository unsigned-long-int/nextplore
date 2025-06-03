from typing import Dict, Any, Optional
from pydantic import BaseModel

class IntegrationCreateRequest(BaseModel):
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
    extra_options: Optional[Dict[str, Any]]
