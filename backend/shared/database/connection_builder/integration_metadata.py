from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrationMetadata:
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
